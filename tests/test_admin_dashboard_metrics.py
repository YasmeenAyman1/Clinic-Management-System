def test_admin_dashboard_shows_pending_and_audits(client, monkeypatch):
    class FakeUserRepo:
        def list_pending_users(self):
            return [1,2,3]
    class FakeAuditRepo:
        def list_recent(self, n):
            class A: pass
            a = A(); a.created_at = '2025-01-01'; a.action='approve_user'; a.admin_user_id=1; a.target_type='doctor'; a.target_user_id=3
            return [a]

    monkeypatch.setattr('src.controllers.authO_controller.RepositoryFactory.get_repository', lambda k: FakeUserRepo() if k=='user' else FakeAuditRepo() if k=='admin_audit' else None, raising=False)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'; sess['status'] = 'active'; sess['user_id'] = 1

    from flask import url_for
    with client.application.test_request_context():
        path = url_for('auth.dashboard')
    res = client.get(path)
    assert res.status_code == 200
    assert b'Pending Approvals' in res.data
    assert b'Recent Admin Actions' in res.data
    assert b'approve_user' in res.data
