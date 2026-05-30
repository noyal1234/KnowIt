nonisolated enum AuthMapper {
    static func toUser(from dto: UserDTO) -> User {
        User(
            id: dto.id,
            email: dto.email,
            displayName: dto.displayName,
            region: dto.region
        )
    }

    static func toTokens(from dto: TokenResponseDTO) -> AuthTokens {
        AuthTokens(accessToken: dto.accessToken, refreshToken: dto.refreshToken)
    }
}
