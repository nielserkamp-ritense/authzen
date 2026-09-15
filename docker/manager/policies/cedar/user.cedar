permit (
    principal is user,
    action == name::"can_read",
    resource is service
)
when {
    principal has roles &&
    (principal.roles == "user" || principal.roles.contains("user"))
};
