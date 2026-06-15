import pytest

from app.core.audit_codes import AuditAction


class TestAuditActionEnum:

    def test_members_have_correct_values(self):
        for member in AuditAction:
            assert member.value == member.name

    def test_value_equals_name(self):
        for member in AuditAction:
            assert member.value == member.name

    def test_iteration_returns_all_members(self):
        members = list(AuditAction)
        assert len(members) >= 7
        assert all(isinstance(m, AuditAction) for m in members)

    def test_invalid_action_raises_value_error(self):
        with pytest.raises(ValueError):
            AuditAction("INVALID_ACTION")

    def test_members_are_strings(self):
        for member in AuditAction:
            assert isinstance(member.value, str)
