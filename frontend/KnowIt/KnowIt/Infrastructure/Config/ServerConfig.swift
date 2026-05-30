import Foundation

@Observable
final class ServerConfig {
    static let shared = ServerConfig()

    private let defaultsKey = "knowit.dev.httpBaseURL"

    var httpBaseURL: String? {
        get { UserDefaults.standard.string(forKey: defaultsKey) }
        set {
            if let newValue, !newValue.isEmpty {
                UserDefaults.standard.set(newValue, forKey: defaultsKey)
            } else {
                UserDefaults.standard.removeObject(forKey: defaultsKey)
            }
        }
    }

    private init() {}
}
