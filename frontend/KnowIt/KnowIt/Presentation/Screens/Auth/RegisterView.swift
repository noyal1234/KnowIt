import SwiftUI

struct RegisterView: View {
    @State private var viewModel: RegisterViewModel
    @Environment(\.dismiss) private var dismiss

    init(viewModel: RegisterViewModel) {
        _viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.l) {
                TextField(String(localized: "auth.displayName"), text: $viewModel.displayName)
                    .textContentType(.name)
                    .padding(AppSpacing.m)
                    .background(AppColor.surfaceCard)
                    .clipShape(RoundedRectangle(cornerRadius: AppRadius.button))

                TextField(String(localized: "auth.email"), text: $viewModel.email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(AppSpacing.m)
                    .background(AppColor.surfaceCard)
                    .clipShape(RoundedRectangle(cornerRadius: AppRadius.button))

                SecureField(String(localized: "auth.password"), text: $viewModel.password)
                    .textContentType(.newPassword)
                    .padding(AppSpacing.m)
                    .background(AppColor.surfaceCard)
                    .clipShape(RoundedRectangle(cornerRadius: AppRadius.button))

                if case .error(let error) = viewModel.state {
                    Text(error.message)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColor.statusError)
                }

                Button {
                    Task {
                        await viewModel.register()
                        if case .loaded = viewModel.state {
                            dismiss()
                        }
                    }
                } label: {
                    Group {
                        if case .loading = viewModel.state {
                            ProgressView().tint(.white)
                        } else {
                            Text(String(localized: "auth.register.action"))
                        }
                    }
                    .frame(maxWidth: .infinity, minHeight: AppSpacing.touchTarget)
                }
                .buttonStyle(.borderedProminent)
                .tint(AppColor.brandPrimary)
            }
            .padding(AppSpacing.screenHorizontal)
        }
        .background(AppColor.surfaceBackground)
        .navigationTitle(String(localized: "auth.register.title"))
    }
}
