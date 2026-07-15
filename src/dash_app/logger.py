from datetime import datetime
from typing import TYPE_CHECKING

from dash_app.messages import (
    LABEL_DIALOGUE,
    LABEL_EFFECTS,
    LABEL_PREDICATES,
    LOG_CHANGE,
    LOG_CREATE,
    LOG_DELETE,
    LOG_FIELD_SEPARATOR,
    LOG_FIELDS_PREFIX,
    LOG_UPDATE,
    NODE_TYPE_NODE,
    NODE_TYPE_NPC,
    NODE_TYPE_PLAYER
)
from dialogue_editor.messages import FIELD_SOURCE, FIELD_TARGET
from dialogue_model.codecs import (
    convert_effect_to_text, convert_predicate_to_text
)

if TYPE_CHECKING:
    from dialogue_editor.graph_editor import GraphEditor

class Logger:
    """Manages formatting and appending log messages with consistent 
    styling.
    """

    def __init__(self, graph_editor: "GraphEditor") -> None:
        """Store graph editor state used to build log field snapshots.
        
        Args:
            graph_editor (GraphEditor): GraphEditor object.
        """
        self.graph_editor = graph_editor

    def append_grouped_status(
        self,
        current_log: list[dict[str, str]] | None,
        lines: list[str],
        level: str = "info"
    ) -> list[dict[str, str]] | None:
        """Append multiple lines as a single multi-line log entry.

        Grouping related lines into one entry keeps their internal order
        stable under reverse-chronological rendering and gives them a shared
        timestamp. This is used wherever one user action produces several
        related lines (e.g., a validation summary with its issue list).

        Args:
            current_log (list[dict[str, str]] | None): Existing log entries.
            lines (list[str]): Ordered lines to combine into one entry.
            level (str): Severity level for the entry (default: "info").

        Returns:
            list[dict[str, str]] | None: Updated log entries, or the original
                log unchanged when no non-empty lines are provided.
        """
        non_empty_lines = [line for line in lines if line]
        if not non_empty_lines:
            return current_log
        return self.append_status(
            current_log, "\n".join(non_empty_lines), level
        )

    def append_status(
        self, 
        current_log: list[dict[str, str]] | None, 
        new_message: str,
        level: str = "info"
    ) -> list[dict[str, str]]:
        """Append a message to the action log.

        Args:
            current_log (list[dict[str, str]] | None): Existing log entries.
            new_message (str): Message to append.
            level (str): Severity level for the entry (default "info").

        Returns:
            list[dict[str, str]]: Updated list of log entries.
        """
        entries = list(current_log) if current_log else []
        entries.append(self.build_log_entry(new_message, level))
        return entries

    def build_create_log(
        self, 
        node_type: str, 
        node_id: str, 
        fields: list[tuple[str, str | None]]
    ) -> str:
        """Build a create-action log line.

        Args:
            node_type (str): Friendly node type label.
            node_id (str): Node identifier.
            fields (list[tuple[str, str | None]]): Field/value pairs.

        Returns:
            str: User-facing create log line.
        """
        base_message = LOG_CREATE.format(
            node_type=node_type, node_value=self.quote_value(node_id)
        )
        return f"{base_message}{self.format_fields(fields)}."

    def build_delete_log(
        self, 
        node_type: str, 
        node_id: str, 
        fields: list[tuple[str, str | None]]
    ) -> str:
        """Build a delete-action log line.

        Args:
            node_type (str): Friendly node type label.
            node_id (str): Node identifier.
            fields (list[tuple[str, str | None]]): Field/value pairs.

        Returns:
            str: User-facing delete log line.
        """
        base_message = LOG_DELETE.format(
            node_type=node_type, node_value=self.quote_value(node_id)
        )
        return f"{base_message}{self.format_fields(fields)}."

    def build_log_entry(
        self, message: str, level: str = "info"
    ) -> dict[str, str]:
        """Build a single structured log entry, carrying the message, severity
        level, and a timestamp.

        Args:
            message (str): User-facing log message.
            level (str): Severity level for the entry (default "info").

        Returns:
            dict[str, str]: Structured log entry.
        """
        return {
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        }

    def build_update_log(
        self,
        node_type: str,
        node_id: str,
        before_fields: list[tuple[str, str | None]],
        after_fields: list[tuple[str, str | None]]
    ) -> str:
        """Build an update-action log line with changed fields only.

        Args:
            node_type (str): Friendly node type label.
            node_id (str): Node identifier.
            before_fields (list[tuple[str, str | None]]): Values before save.
            after_fields (list[tuple[str, str | None]]): Values after save.

        Returns:
            str: User-facing update log line.
        """
        change_fragments = []
        for (field_name, old_value), (_, new_value) in zip(
            before_fields, after_fields
        ):
            if old_value == new_value:
                continue
            if old_value is None or new_value is None:
                continue
            change_fragments.append(
                LOG_CHANGE.format(
                    field=field_name, 
                    old_value=self.quote_value(old_value),
                    new_value=self.quote_value(new_value)
                )
            )
        base_message = LOG_UPDATE.format(
            node_type=node_type, node_value=self.quote_value(node_id)
        )
        if not change_fragments:
            return f"{base_message}."
        return f"{base_message}: {LOG_FIELD_SEPARATOR.join(change_fragments)}."

    def format_fields(
        self, fields: list[tuple[str, str | None]]
    ) -> str:
        """Format ordered field/value pairs as one log fragment.

        Args:
            fields (list[tuple[str, str | None]]): Ordered field/value pairs.

        Returns:
            str: Formatted field/value fragment.
        """
        present_fields = [
            f"{field_name} {self.quote_value(field_value)}"
            for field_name, field_value in fields
            if field_value is not None
        ]
        if not present_fields:
            return ""
        return LOG_FIELDS_PREFIX + LOG_FIELD_SEPARATOR.join(present_fields)

    def get_node_log_fields(
        self,
        node_id: str,
        include_empty: bool = False
    ) -> tuple[str, list[tuple[str, str | None]]]:
        """Return a node type label and ordered fields for logging.

        Args:
            node_id (str): Node identifier.
            include_empty (bool): Include empty values when "True".

        Returns:
            tuple[str, list[tuple[str, str | None]]]: Node type label and
                ordered field/value pairs.
        """
        if node_id in self.graph_editor.graph.vertex_dict:
            return (
                NODE_TYPE_NPC, self.get_npc_log_fields(node_id, include_empty)
            )
        if node_id in self.graph_editor.graph.edge_dict:
            return (
                NODE_TYPE_PLAYER,
                self.get_player_log_fields(node_id, include_empty)
            )
        return NODE_TYPE_NODE, []

    def get_npc_log_fields(
        self,
        node_id: str,
        include_empty: bool = False
    ) -> list[tuple[str, str | None]]:
        """Reteurn NPC node fields for logging.

        Args:
            node_id (str): NPC node identifier.
            include_empty (bool): Include empty values when "True".

        Returns:
            list[tuple[str, str | None]]: Ordered field/value pairs.
        """
        vertex = self.graph_editor.graph.vertex_dict[node_id]
        return [
            (
                LABEL_DIALOGUE,
                self.serialize_text_value(vertex.text, include_empty)
            ),
            (
                LABEL_EFFECTS,
                self.serialize_effects_value(vertex.effects, include_empty)
            )
        ]

    def get_player_log_fields(
        self,
        node_id: str,
        include_empty: bool = False
    ) -> list[tuple[str, str | None]]:
        """Return Player node fields for logging.

        Args:
            node_id (str): Player node identifier.
            include_empty (bool): Include empty values when "True".

        Returns:
            list[tuple[str, str | None]]: Ordered field/value pairs.
        """
        edge = self.graph_editor.graph.edge_dict[node_id]
        return [
            (
                LABEL_DIALOGUE,
                self.serialize_text_value(edge.text, include_empty)
            ),
            (
                FIELD_SOURCE,
                self.serialize_text_value(edge.from_vertex, include_empty)
            ),
            (
                FIELD_TARGET,
                self.serialize_text_value(edge.to_vertex, include_empty)
            ),
            (
                LABEL_PREDICATES,
                self.serialize_predicates_value(edge.predicates, include_empty)
            ),
            (
                LABEL_EFFECTS,
                self.serialize_effects_value(edge.effects, include_empty)
            )
        ]

    def serialize_effects_value(
        self,
        effects: list[dict[str, str | int]] | None,
        include_empty: bool = False
    ) -> str | None:
        """Serialize effects using the user-facing line format.

        Args:
            effects (list[dict[str, str | int]] | None): Effect mappings.
            include_empty (bool): Include empty lists when "True".

        Returns:
            str | None: Serialized effects text.
        """
        if effects is None:
            return None
        if not effects:
            return "" if include_empty else None
        return LOG_FIELD_SEPARATOR.join(
            convert_effect_to_text(effect) for effect in effects
        )

    def serialize_predicates_value(
        self,
        predicates: list[dict[str, str | int]] | None,
        include_empty: bool = False
    ) -> str | None:
        """Serialize predicates using the user-facing line format.

        Args:
            predicates (list[dict[str, str | int]] | None): Predicate mappings.
            include_empty (bool): Include empty lists when "True".

        Returns:
            str | None: Serialized predicates text.
        """
        if predicates is None:
            return None
        if not predicates:
            return "" if include_empty else None
        return LOG_FIELD_SEPARATOR.join(
            convert_predicate_to_text(predicate) for predicate in predicates
        )

    def serialize_text_value(
        self, value: str | None, include_empty: bool = False
    ) -> str | None:
        """Serialize a text value for the logs.

        Args:
            value (str | None): Candidate text value.
            include_empty (bool): Include empty strings when "True".

        Returns:
            str | None: Serialized value or None when omitted.
        """
        if value is None:
            return None
        if value == "" and not include_empty:
            return None
        return value

    def quote_value(self, value: str) -> str:
        """Return a safely quoted value for the logs.

        Args:
            value (str): Value to quote.

        Returns:
            str: Escaped value wrapped in quotes.
        """
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'