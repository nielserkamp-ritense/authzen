forbid (
    principal is user,
    action == name::"can_update",
    resource is service
)
when {
    context has http &&
    context.http has path &&
    context.http.path == "/v1/deployment"
}
unless {
    principal has roles &&
    (principal.roles == "admin" || principal.roles.contains("admin"))
};
