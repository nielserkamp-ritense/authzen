permit (
    principal is user,
    action,
    resource is service
)
when {
    principal has roles &&
    (principal.roles == "author" || principal.roles.contains("author"))
};
