import SwiftUI

struct ServerConfigView: View {
    @State private var baseURL = ServerConfig.shared.httpBaseURL ?? AppConfig.apiBaseURL.absoluteString
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        Form {
            Section(String(localized: "devtools.server.section")) {
                TextField(String(localized: "devtools.server.url"), text: $baseURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
            }
            Section {
                Button(String(localized: "devtools.server.save")) {
                    ServerConfig.shared.httpBaseURL = baseURL
                    dismiss()
                }
                Button(String(localized: "devtools.server.reset"), role: .destructive) {
                    ServerConfig.shared.httpBaseURL = nil
                    baseURL = AppConfig.apiBaseURL.absoluteString
                }
            }
        }
        .navigationTitle(String(localized: "devtools.server.title"))
        .navigationBarTitleDisplayMode(.inline)
    }
}
