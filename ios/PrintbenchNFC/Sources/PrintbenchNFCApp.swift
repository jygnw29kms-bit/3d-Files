import SwiftUI

@main
struct PrintbenchNFCApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}

struct ContentView: View {
    @StateObject private var nfcWriter = NFCWriter()
    @State private var showingScanner = false
    @State private var payload: PrintbenchSpoolPayload?
    @State private var errorText: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    header
                    statusCard
                    if let payload { spoolCard(payload) } else { emptyCard }

                    Button {
                        showingScanner = true
                    } label: {
                        Label("PRINTBENCH QR scannen", systemImage: "qrcode.viewfinder")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                    }
                    .buttonStyle(.borderedProminent)

                    if let payload {
                        Button {
                            nfcWriter.write(payload)
                        } label: {
                            Label(nfcWriter.isWriting ? "NFC wird beschrieben …" : "NTAG216 schreiben", systemImage: "wave.3.right")
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 14)
                        }
                        .buttonStyle(.bordered)
                        .disabled(nfcWriter.isWriting)
                    }

                    if let errorText {
                        Text(errorText)
                            .font(.footnote)
                            .foregroundStyle(.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding()
            }
            .navigationTitle("PRINTBENCH NFC")
            .sheet(isPresented: $showingScanner) {
                NavigationStack {
                    QRScannerView { text in
                        do {
                            payload = try PrintbenchSpoolPayload.decode(scannedText: text)
                            errorText = nil
                            showingScanner = false
                        } catch {
                            errorText = error.localizedDescription
                            showingScanner = false
                        }
                    }
                    .ignoresSafeArea()
                    .navigationTitle("Spool QR")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Abbrechen") { showingScanner = false }
                        }
                    }
                }
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Spool → NFC")
                .font(.system(size: 28, weight: .bold, design: .rounded))
            Text("QR aus PRINTBENCH scannen, NTAG216 beschreiben, zurücklesen und die echte UID automatisch mit der Spule verknüpfen.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("NFC Status", systemImage: "dot.radiowaves.left.and.right")
                .font(.headline)
            Text(nfcWriter.status)
                .font(.callout)
                .foregroundStyle(.secondary)
            if nfcWriter.serverLinked {
                Label("UID mit PRINTBENCH verknüpft", systemImage: "checkmark.shield.fill")
                    .font(.caption.bold())
                    .foregroundStyle(.green)
            }
            if let uid = nfcWriter.lastUID {
                Text("UID  \(uid)")
                    .font(.system(.caption, design: .monospaced))
                    .textSelection(.enabled)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
    }

    private var emptyCard: some View {
        VStack(spacing: 10) {
            Image(systemName: "shippingbox")
                .font(.system(size: 42))
                .foregroundStyle(.secondary)
            Text("Noch keine Spule geladen")
                .font(.headline)
            Text("Erzeuge in PRINTBENCH einen Spool-QR-Code und scanne ihn hier.")
                .font(.footnote)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
        }
        .padding(24)
        .frame(maxWidth: .infinity)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
    }

    private func spoolCard(_ payload: PrintbenchSpoolPayload) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(payload.displayName ?? payload.spoolId)
                .font(.title3.bold())
            LabeledContent("Spool-ID", value: payload.spoolId)
            if let vendor = payload.vendor { LabeledContent("Hersteller", value: vendor) }
            if let material = payload.material { LabeledContent("Material", value: material) }
            if let color = payload.colorHex { LabeledContent("Farbe", value: color) }
            Text("Auf dem Tag werden nur stabile Identitätsdaten gespeichert. Restgewicht, Trocknung, Kosten und Historie bleiben in PRINTBENCH.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(.top, 4)
            if let expires = payload.expiresAt {
                Text("NFC-Claim gültig bis: \(expires)")
                    .font(.caption2.monospaced())
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
    }
}