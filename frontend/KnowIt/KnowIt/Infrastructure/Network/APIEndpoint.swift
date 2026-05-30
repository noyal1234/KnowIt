import Foundation

nonisolated enum APIEndpoint: RequestBuildable {
    case login(email: String, password: String)
    case register(email: String, password: String, displayName: String)
    case refreshToken(refreshToken: String)
    case logout(refreshToken: String)
    case me

    var path: String {
        switch self {
        case .login: return "/v1/auth/login"
        case .register: return "/v1/auth/register"
        case .refreshToken: return "/v1/auth/refresh"
        case .logout: return "/v1/auth/logout"
        case .me: return "/v1/auth/me"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .login, .register, .refreshToken, .logout: return .POST
        case .me: return .GET
        }
    }

    var body: Encodable? {
        switch self {
        case let .login(email, password):
            return LoginRequestDTO(email: email, password: password)
        case let .register(email, password, displayName):
            return RegisterRequestDTO(email: email, password: password, displayName: displayName)
        case let .refreshToken(refreshToken):
            return RefreshRequestDTO(refreshToken: refreshToken)
        case let .logout(refreshToken):
            return RefreshRequestDTO(refreshToken: refreshToken)
        case .me:
            return nil
        }
    }

    var timeout: TimeInterval {
        switch self {
        case .login, .register: return 20
        default: return 30
        }
    }

    var retryPolicy: RetryPolicy {
        switch self {
        case .login, .register, .refreshToken, .logout: return .none
        default: return .exponential(maxAttempts: 3)
        }
    }

    var requiresAuth: Bool {
        switch self {
        case .login, .register, .refreshToken: return false
        default: return true
        }
    }
}
