import Foundation

struct StoredToken: Sendable {
    let accessToken: String
    let refreshToken: String

    static let empty = StoredToken(accessToken: "", refreshToken: "")

    var isLoggedIn: Bool {
        !accessToken.isEmpty || !refreshToken.isEmpty
    }
}
