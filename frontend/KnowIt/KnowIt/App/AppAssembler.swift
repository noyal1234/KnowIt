import Foundation
import OSLog

@MainActor
final class AppAssembler {
    let tokenStore: TokenStore
    let apiClient: APIClient
    let authRepository: AuthRepository
    let loginUseCase: LoginUseCase
    let registerUseCase: RegisterUseCase
    let fetchCurrentUserUseCase: FetchCurrentUserUseCase
    let logoutUseCase: LogoutUseCase
    let rootViewModel: RootViewModel

    init() {
        let tokenStore = TokenStore()
        self.tokenStore = tokenStore

        let apiClient = APIClient(tokenStore: tokenStore)
        self.apiClient = apiClient

        let authRemote = AuthRemoteDataSource(apiClient: apiClient)
        let authRepository = AuthRepository(remote: authRemote, tokenStore: tokenStore)
        self.authRepository = authRepository

        tokenStore.refreshHandler = { [authRepository] in
            try await authRepository.refreshSession()
        }

        let loginUseCase = LoginUseCase(repository: authRepository)
        self.loginUseCase = loginUseCase
        let registerUseCase = RegisterUseCase(repository: authRepository)
        self.registerUseCase = registerUseCase
        let fetchCurrentUserUseCase = FetchCurrentUserUseCase(repository: authRepository)
        self.fetchCurrentUserUseCase = fetchCurrentUserUseCase
        let logoutUseCase = LogoutUseCase(repository: authRepository)
        self.logoutUseCase = logoutUseCase

        self.rootViewModel = RootViewModel(
            fetchCurrentUser: fetchCurrentUserUseCase,
            authRepository: authRepository
        )

        AppLogger.general.notice("event=AppAssemblerReady")
    }

    func makeLoginViewModel(onSuccess: @escaping () -> Void) -> LoginViewModel {
        LoginViewModel(loginUseCase: loginUseCase, onSuccess: onSuccess)
    }

    func makeRegisterViewModel(onSuccess: @escaping () -> Void) -> RegisterViewModel {
        RegisterViewModel(registerUseCase: registerUseCase, onSuccess: onSuccess)
    }

    func makeHomeViewModel(user: User, onLogout: @escaping () -> Void) -> HomeViewModel {
        HomeViewModel(user: user, onLogout: onLogout)
    }

    static let preview = AppAssembler()
}
