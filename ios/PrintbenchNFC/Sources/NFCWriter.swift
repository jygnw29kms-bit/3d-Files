import Foundation
import CoreNFC

@MainActor
final class NFCWriter: NSObject, ObservableObject {
    @Published var status = "Bereit"
    @Published var lastUID: String?
    @Published var isWriting = false
    @Published var serverLinked = false

    private var session: NFCTagReaderSession?
    private var payload: PrintbenchSpoolPayload?

    func write(_ payload: PrintbenchSpoolPayload) {
        guard NFCTagReaderSession.readingAvailable else {
            status = "NFC wird auf diesem iPhone nicht unterstützt."
            return
        }
        guard payload.claimEndpoint != nil else {
            status = "Der QR-Code enthält keinen gültigen PRINTBENCH-Claim. Bitte einen neuen QR-Code erzeugen."
            return
        }

        self.payload = payload
        self.isWriting = true
        self.serverLinked = false
        self.status = "iPhone an den NTAG216 halten …"

        guard let session = NFCTagReaderSession(pollingOption: [.iso14443], delegate: self, queue: nil) else {
            self.isWriting = false
            self.status = "NFC-Session konnte nicht gestartet werden."
            return
        }
        session.alertMessage = "PRINTBENCH: iPhone an den NTAG216 der Spule halten."
        self.session = session
        session.begin()
    }

    private func uidHex(_ data: Data) -> String {
        data.map { String(format: "%02X", $0) }.joined(separator: ":")
    }

    private func registerUID(_ uid: String, payload: PrintbenchSpoolPayload) async {
        guard let url = payload.claimEndpoint else {
            status = "Tag geschrieben, aber Claim-URL fehlt. Bitte neuen QR-Code erzeugen."
            return
        }
        do {
            status = "Tag verifiziert · UID wird mit PRINTBENCH verknüpft …"
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.timeoutInterval = 15
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: ["uid": uid, "tagType": "NTAG216"])
            let (data, response) = try await URLSession.shared.data(for: request)
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            guard (200..<300).contains(code) else {
                let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["error"] as? String ?? "HTTP \(code)"
                throw LinkError.server(detail)
            }
            serverLinked = true
            status = "Fertig · NTAG216 geschrieben, verifiziert und UID in PRINTBENCH gespeichert."
        } catch {
            serverLinked = false
            status = "Tag ist geschrieben, aber UID-Verknüpfung fehlgeschlagen: \(error.localizedDescription). Neuen QR-Code erzeugen und erneut verknüpfen."
        }
    }

    private enum LinkError: LocalizedError {
        case server(String)
        var errorDescription: String? {
            switch self { case .server(let text): return text }
        }
    }
}

extension NFCWriter: NFCTagReaderSessionDelegate {
    nonisolated func tagReaderSessionDidBecomeActive(_ session: NFCTagReaderSession) {}

    nonisolated func tagReaderSession(_ session: NFCTagReaderSession, didInvalidateWithError error: Error) {
        Task { @MainActor in
            self.isWriting = false
            let nsError = error as NSError
            if nsError.code != NFCReaderError.readerSessionInvalidationErrorUserCanceled.rawValue {
                self.status = "NFC abgebrochen: \(error.localizedDescription)"
            }
        }
    }

    nonisolated func tagReaderSession(_ session: NFCTagReaderSession, didDetect tags: [NFCTag]) {
        guard tags.count == 1 else {
            session.alertMessage = "Bitte nur einen NFC-Tag an das iPhone halten."
            session.restartPolling()
            return
        }
        guard case let .miFare(tag) = tags[0] else {
            session.invalidate(errorMessage: "Der erkannte Tag ist kein unterstützter ISO14443/MIFARE-kompatibler NFC-Tag.")
            return
        }

        Task { @MainActor in
            guard let payload = self.payload else {
                session.invalidate(errorMessage: "Kein PRINTBENCH-Spool-Datensatz geladen.")
                return
            }
            session.connect(to: tags[0]) { error in
                if let error {
                    session.invalidate(errorMessage: "NFC-Verbindung fehlgeschlagen: \(error.localizedDescription)")
                    return
                }
                tag.queryNDEFStatus { status, capacity, error in
                    if let error {
                        session.invalidate(errorMessage: "NDEF-Status konnte nicht gelesen werden: \(error.localizedDescription)")
                        return
                    }
                    guard status == .readWrite else {
                        session.invalidate(errorMessage: "Der NFC-Tag ist nicht beschreibbar.")
                        return
                    }
                    var records: [NFCNDEFPayload] = []
                    if let url = payload.canonicalURL,
                       let urlRecord = NFCNDEFPayload.wellKnownTypeURIPayload(url: url) { records.append(urlRecord) }
                    if let json = payload.compactJSON,
                       let text = String(data: json, encoding: .utf8),
                       let textRecord = NFCNDEFPayload.wellKnownTypeTextPayload(string: text, locale: Locale(identifier: "de_DE")) { records.append(textRecord) }
                    let message = NFCNDEFMessage(records: records)
                    guard !records.isEmpty, message.length <= capacity else {
                        session.invalidate(errorMessage: "PRINTBENCH-Datensatz ist größer als die NFC-Kapazität.")
                        return
                    }
                    tag.writeNDEF(message) { error in
                        if let error {
                            session.invalidate(errorMessage: "Schreiben fehlgeschlagen: \(error.localizedDescription)")
                            return
                        }
                        tag.readNDEF { writtenMessage, error in
                            if let error {
                                session.invalidate(errorMessage: "Tag wurde geschrieben, konnte aber nicht verifiziert werden: \(error.localizedDescription)")
                                return
                            }
                            guard let writtenMessage, writtenMessage.records.count == records.count else {
                                session.invalidate(errorMessage: "NFC-Verifikation fehlgeschlagen.")
                                return
                            }
                            let uid = self.uidHex(tag.identifier)
                            session.alertMessage = "PRINTBENCH-Tag geschrieben und verifiziert. UID: \(uid)"
                            session.invalidate()
                            Task { @MainActor in
                                self.lastUID = uid
                                self.isWriting = false
                                await self.registerUID(uid, payload: payload)
                            }
                        }
                    }
                }
            }
        }
    }
}