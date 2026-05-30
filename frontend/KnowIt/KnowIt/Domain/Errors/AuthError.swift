enum AuthError: Error, LocalizedError, Sendable {
    case invalidCredentials
    case sessionExpired
    case registrationFailed(message: String)
    case network(underlying: NetworkError)

    var errorDescription: String? {
        switch self {
        case .invalidCredentials:
            return "Invalid email or password."
        case .sessionExpired:
            return "Your session has expired. Please log in again."
        case .registrationFailed(let message):
            return message
        case .network(let error):
            return error.localizedDescription
        }
    }
}
