import Foundation

struct PrintbenchSpoolPayload: Codable, Equatable {
    let version: Int
    let spoolId: String
    let displayName: String?
    let material: String?
    let vendor: String?
    let colorHex: String?
    let claimURL: String?
    let signature: String?
    let expiresAt: String?

    static func decode(scannedText: String) throws -> PrintbenchSpoolPayload {
        if let data = scannedText.data(using: .utf8),
           let payload = try? JSONDecoder().decode(PrintbenchSpoolPayload.self, from: data),
           !payload.spoolId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return payload
        }

        guard let components = URLComponents(string: scannedText),
              let spoolId = components.queryItems?.first(where: { $0.name == "spool" })?.value,
              !spoolId.isEmpty else {
            throw PayloadError.invalidQR
        }

        let signature = components.queryItems?.first(where: { $0.name == "sig" })?.value
        return PrintbenchSpoolPayload(
            version: 1,
            spoolId: spoolId,
            displayName: nil,
            material: nil,
            vendor: nil,
            colorHex: nil,
            claimURL: scannedText,
            signature: signature,
            expiresAt: nil
        )
    }

    var canonicalURL: URL? {
        URL(string: "https://www.dezender.de/3d-druck/spool/?spool=\(spoolId.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? spoolId)")
    }

    var claimEndpoint: URL? {
        guard let claimURL else { return nil }
        return URL(string: claimURL)
    }

    var compactJSON: Data? {
        let minimal = MinimalTagPayload(version: version, spoolId: spoolId)
        return try? JSONEncoder().encode(minimal)
    }

    private struct MinimalTagPayload: Codable {
        let version: Int
        let spoolId: String
    }

    enum PayloadError: LocalizedError {
        case invalidQR
        var errorDescription: String? {
            "Der QR-Code enthält keinen gültigen PRINTBENCH-Spool-Datensatz."
        }
    }
}