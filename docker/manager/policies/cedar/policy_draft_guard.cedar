forbid (
    principal is user,
    action == name::"can_update",
    resource is service
)
when {
    resource has status && resource.status != "draft"
}
unless {
    principal has roles && (principal.roles == "admin" || principal.roles.contains("admin"))
};
