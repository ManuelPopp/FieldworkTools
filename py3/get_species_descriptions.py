import re
import pykew.powo as powo
from pykew.powo_terms import Name, Filters

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)

def flatten_object(obj, level = 0, clean = True, exclude_tags = None):
    """
    Flatten a nested object into a string representation.
    
    Parameters
    ----------
    obj : dict | list | str
        The object to flatten.
    level : int
        The current level of nesting (used for indentation).
    clean : bool
        Whether to remove HTML tags from the flattened output.
    exclude_tags : list
        A list of tags to exclude from the flattened output.
        Supports regular expressions.
    
    Returns
    -------
    str
        The flattened string representation of the object.
    """
    if exclude_tags is None:
        exclude_tags = []
    if isinstance(obj, dict):
        parts = []
        for k, v in obj.items():
            if any(
                re.fullmatch(
                    pattern.replace("*", ".*"), k, re.IGNORECASE
                    ) for pattern in exclude_tags
                ):
                continue
            parts.append(
                f"{k}: {flatten_object(v, level + 1, clean, exclude_tags)}"
                )
        return "\n\n".join(parts)
    elif isinstance(obj, list):
        return "\n".join(
            flatten_object(v, level + 1, clean, exclude_tags) for v in obj
            )
    else:
        return strip_html(str(obj)) if clean else str(obj)

def get_descriptions(
        name = None, genus = None, epithet = None, flatten = True, **kwargs
        ):
    """
    Get descriptions for a plant species from kew.org.
    Either the name as a single string or both genus and epithet must be
    provided.

    Parameters
    ----------
    name : str | None
        The common name of the plant.
    genus : str | None
        The genus of the plant.
    epithet : str | None
        The species epithet of the plant.
    flatten : bool
        Whether to remove HTML tags from the flattened output.
    **kwargs : dict
        Additional keyword arguments to pass to the flatten function.
    
    Returns
    -------
    list
        A list of descriptions found in the query results.
    """
    if name:
        results = powo.search(name)
    elif genus and epithet:
        query = {Name.genus: genus, Name.species: epithet}
        results = powo.search(
            query, filters = [Filters.accepted, Filters.species]
            )
    else:
        raise ValueError(
            "Either name or both genus and epithet must be provided."
            )
    
    descriptions = []
    for result in results:
        fqid = result["fqId"]
        details = powo.lookup(fqid, include = ["descriptions"])
        description = (
            details.get("descriptions") or details.get("description") or "N/A"
        )
        descriptions.append(description)
    
    return flatten_object(descriptions, **kwargs) if flatten else descriptions

# Usage example
if __name__ == "__main__":
    description = get_descriptions(name = "Bellis perennis")
    print(description)