enum ViewState<T: Sendable>: Sendable, Equatable where T: Equatable {
    case idle
    case loading
    case loaded(T)
    case empty
    case error(AppError)
}
