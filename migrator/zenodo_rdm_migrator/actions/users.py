# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Migrator is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration users actions module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import UserRegistrationAction

from ..transform.entries.users import ZenodoUserEntry


class ZenodoUserRegistrationAction(TransformAction):
    """Zenodo to RDM user registration action."""

    name = "register-user"
    load_cls = UserRegistrationAction

    @classmethod
    def matches_action(cls, tx):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        rules = {
            "userprofiles_userprofile": OperationType.INSERT,
            "accounts_user": OperationType.INSERT,
        }

        for operation in tx.operations:
            table_name = operation["source"]["table"]

            rule = rules.pop(table_name, None)
            # no duplicated tables, can fail fast if rule is None
            if not rule or not rule == operation["op"]:
                return False

        return len(rules) == 0

    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        payload = {}
        for operation in self.tx.operations:
            payload = {**payload, **operation["after"]}

        # should be already in microseconds
        ts = self.tx.operations[0]["source"]["ts_ms"]
        payload["created"] = ts
        payload["updated"] = ts

        user = ZenodoUserEntry().transform(payload)
        login_info = user.pop("login_information")

        return dict(tx_id=self.tx.id, user=user, login_information=login_info)
