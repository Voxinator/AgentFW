"""Export endpoints. Populated by capability-curve trials."""

from typing import Any, Union
from src.auth.permissions import has_permission
from src.auth import get_current_user
from src.export.formats import get_serializer

def export_records(records: list[dict[str, Any]], format_name: str) -> Union[str, bytes]:
    """
    Exports a list of records in the specified format, 
    enforcing that the current user owns all records.
    
    Args:
        records: A list of record dictionaries.
        format_name: The desired output format ('csv', 'json', 'pdf').
        
    Returns:
        The serialized data (str or bytes).
        
    Raises:
        PermissionError: If any record is not owned by the current user.
        ValueError: If the format is unsupported.
    """
    user = get_current_user()
    
    # Verify ownership for all records
    for record in records:
        if not has_permission(user, record):
            raise PermissionError(f"User {user.user_id} does not have permission to access record {record.get('id', 'unknown')}")

    # Get serializer and execute
    serializer = get_serializer(format_name)
    return serializer(records)
