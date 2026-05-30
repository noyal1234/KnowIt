import Foundation

@Observable
@MainActor
final class RootViewModel {
    enum Phase: Equatable, Sendable {
        case bootstrapping
        case unauthenticated
        case authenticated(User)
    }

    private(set) var phase: Phase = .bootstrapping
    private let fetchCurrentUser: FetchCurrentUserUseCase
    private let authRepository: AuthRepositoryProtocol

    init(fetchCurrentUser: FetchCurrentUserUseCase, authRepository: AuthRepositoryProtocol) {
        self.fetchCurrentUser = fetchCurrentUser
        self.authRepository = authRepository
    }

    func resolveInitialRoute() async {
        guard authRepository.isLoggedIn else {
            phase = .unauthenticated
            return
        }
        do {
            let user = try await fetchCurrentUser.execute()
            phase = .authenticated(user)
        } catch {
            phase = .unauthenticated
        }
    }

    func markAuthenticated(_ user: User) {
        phase = .authenticated(user)
    }

    func markLoggedOut() {
        phase = .unauthenticated
    }
}
