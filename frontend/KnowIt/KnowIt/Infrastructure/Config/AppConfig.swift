import Foundation

nonisolated enum AppConfig {
    static let appName = "KnowIt"
    static let platform = "ios"

    static var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0.0.0"
    }

    static var buildNumber: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "0"
    }

    static var apiBaseURL: URL {
        let devBaseURLKey = "knowit.dev.httpBaseURL"
        if let override = UserDefaults.standard.string(forKey: devBaseURLKey),
           !override.isEmpty,
           let url = URL(string: override) {
            return url
        }
        #if DEBUG
        return URL(string: "http://127.0.0.1:8000")!
        #else
        return URL(string: "https://api.knowit.app")!
        #endif
    }
}
