import Foundation

nonisolated struct LoginRequestDTO: Encodable, Sendable {
    let email: String
    let password: String
}

nonisolated struct RegisterRequestDTO: Encodable, Sendable {
    let email: String
    let password: String
    let displayName: String
}

nonisolated struct RefreshRequestDTO: Encodable, Sendable {
    let refreshToken: String
}

nonisolated struct TokenResponseDTO: Decodable, Sendable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
}

nonisolated struct UserDTO: Decodable, Sendable {
    let id: UUID
    let email: String
    let displayName: String
    let region: String
}

nonisolated struct ErrorDetailDTO: Decodable, Sendable {
    let detail: String
}
