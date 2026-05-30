import SwiftUI

struct LoginView: View {
    @State private var viewModel: LoginViewModel

    init(viewModel: LoginViewModel) {
        _viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        content
            .padding(AppSpacing.screenHorizontal)
            .background(AppColor.surfaceBackground)
            .navigationTitle(String(localized: "auth.login.title"))
            .navigationBarTitleDisplayMode(.large)
    }

    @ViewBuilder
    private var content: some View {
        VStack(alignment: .leading, spacing: AppSpacing.l) {
            Text(String(localized: "auth.login.subtitle"))
                .font(AppTypography.bodySmall)
                .foregroundStyle(AppColor.textSecondary)

            VStack(spacing: AppSpacing.m) {
                TextField(String(localized: "auth.email"), text: $viewModel.email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(AppSpacing.m)
                    .background(AppColor.surfaceCard)
                    .clipShape(RoundedRectangle(cornerRadius: AppRadius.button))

                SecureField(String(localized: "auth.password"), text: $viewModel.password)
                    .textContentType(.password)
                    .padding(AppSpacing.m)
                    .background(AppColor.surfaceCard)
                    .clipShape(RoundedRectangle(cornerRadius: AppRadius.button))
            }

            if case .error(let error) = viewModel.state {
                Text(error.message)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColor.statusError)
            }

            Button {
                Task { await viewModel.login() }
            } label: {
                Group {
                    if case .loading = viewModel.state {
                        ProgressView()
                            .tint(.white)
                    } else {
                        Text(String(localized: "auth.login.action"))
                    }
                }
                .frame(maxWidth: .infinity, minHeight: AppSpacing.touchTarget)
            }
            .buttonStyle(.borderedProminent)
            .tint(AppColor.brandPrimary)
            .disabled(viewModel.state == .loading)

            NavigationLink(value: AppRoute.register) {
                Text(String(localized: "auth.register.prompt"))
                    .font(AppTypography.bodySmall)
            }

            Spacer()
        }
    }
}

#Preview {
    NavigationStack {
        LoginView(viewModel: .preview())
    }
}
