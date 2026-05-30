import Foundation

struct LoginRequestDTO: Encodable, Sendable {
    let email: String
    let password: String
}

struct RegisterRequestDTO: Encodable, Sendable {
    let email: String
    let password: String
    let displayName: String
}

struct RefreshRequestDTO: Encodable, Sendable {
    let refreshToken: String
}

struct TokenResponseDTO: Decodable, Sendable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
}

struct UserDTO: Decodable, Sendable {
    let id: UUID
    let email: String
    let displayName: String
    let region: String
}

struct ErrorDetailDTO: Decodable, Sendable {
    let detail: String
}
