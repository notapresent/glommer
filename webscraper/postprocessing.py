"""Functions for post-processing urls and url sets"""
import re


COMMON_RESOLUTIONS = ['hd_720', 'sd_480', 'sd_360', 'sd_240']

res_rx = re.compile('^(?P<prefix>.+)(?P<res>{})(?P<suffix>.+)$'.format('|'.join(COMMON_RESOLUTIONS)), re.I)


def postprocess_items(urlsets):
    deduplicate_urlsets(urlsets)
    if urlsets.get('streaming'):
        urlsets['streaming'] = highest_resolution(urlsets['streaming'])

    return {set_name: set_urls for set_name, set_urls in urlsets.items() if set_urls}


def deduplicate_urlsets(urlsets):
    seen = set()
    for set_name in urlsets.keys():
        urlsets[set_name] = [url for url in urlsets[set_name] if url not in seen]
        seen = seen | set(urlsets[set_name])


def highest_resolution(urls):
    """Filter out all movie versions except for highest-resolution ones"""
    groups, ungrouped = group_by_resolution(urls)

    for group in groups.values():
        best = highest_res_from_group(group)
        ungrouped.append(best)

    return ungrouped


def highest_res_from_group(versions_dict):  # versions_dict == {resolution: url, ...}
    top_key = sorted(versions_dict.keys(), key=COMMON_RESOLUTIONS.index)[0]
    return versions_dict[top_key]


def group_by_resolution(urls):
    all_groups, ungrouped = {}, []

    for url in urls:
        matches = res_rx.fullmatch(url)

        if matches is None:
            ungrouped.append(url)
            continue

        prefix, res, suffix = matches.groups()
        groupname = prefix + suffix

        if groupname in all_groups:
            all_groups[groupname][res] = url
        else:
            all_groups[groupname] = {res: url}

    # if there is only 1 element in gooup then move it to ungrouped
    valid_groups = {}
    for group_name, group in all_groups.items():
        if len(group) > 1:
            valid_groups[group_name] = group
        else:
            url, = group.values()
            ungrouped.append(url)

    return valid_groups, ungrouped
