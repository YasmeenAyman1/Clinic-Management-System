class AdminAudit:
    def __init__(self, id, admin_user_id, action, target_user_id, target_type, details, created_at):
        self.id = id
        self.admin_user_id = admin_user_id
        self.action = action
        self.target_user_id = target_user_id
        self.target_type = target_type
        self.details = details
        self.created_at = created_at
