import frappe

from frappe.utils.safe_exec import get_safe_globals


@frappe.whitelist(allow_guest=True)
def get_serialized_safe_globals():
    """

    safe_globals: a dict of safe globals, might contain child dicts recursively as well.

    e.g.

    {
        "frappe": {
            "get_doc": <function get_doc>,
        },
        "set": <function sorted(iterable, /, *, key=None, reverse=False)>,
        "json": {
            "loads": <function loads>,
            "dumps": <function dumps>
        },
    }

    We want to convert this dict into json object with the following format:

    {
    "frappe": {
        "frappe.get_doc": {
            "type": "function",
            "docs": "Get a document by name or from database if given fields",
            }
        },
    "json": {
        "json.dumps": {
            "type": "function",
            "docs": "Convert a dict to string"
            },
        "json.loads": {
            "type": "function",
            "docs": "Convert a string to dict"
            }
    }
    }

    Get docs only if a function and use the function's docstring.

    If the value is not a dict or function, output just "type": "value" and no docs.
    Also, make sure {"frappe": {"get_doc": ...}} etc. {"frappe": {"frappe.get_doc": ...}} in case of nested dicts.
    """
    import inspect

    safe_globals = get_safe_globals()

    def get_formatted_globals_as_json_helper(safe_globals, prefix=""):
        formatted_globals = {}
        for key, value in safe_globals.items():
            if isinstance(value, dict):
                formatted_globals.update(
                    get_formatted_globals_as_json_helper(value, prefix + key + ".")
                )
            elif callable(value):
                formatted_globals[prefix + key] = {
                    "type": type(value).__name__,
                    "docs": value.__doc__,
                    "is_callable": True,
                    "is_builtin": value.__module__ == "builtins",
                }

                try:
                    function_signature = inspect.signature(value)
                    formatted_globals[prefix + key]["signature"] = str(
                        function_signature
                    )
                    formatted_globals[prefix + key]["parent"] = prefix[:-1]
                except ValueError:
                    # If the function is a builtin function, we can't get the signature
                    pass

            else:
                # if the value is int, str, float, bool, value = value
                # else value will be stringified

                processed_value = value
                if not isinstance(value, (int, str, float, bool)):
                    processed_value = str(value)
                
                    
                formatted_globals[prefix + key] = {
                    "type": type(value).__name__,
                    "value": processed_value,
                    "is_callable": False,
                }
        return formatted_globals

    return get_formatted_globals_as_json_helper(safe_globals)
