"""
The MIT License (MIT)

Copyright (c) 2016 Leonid Runyshkin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


SECTION_START = '{'
SECTION_END = '}'


def loads(data, wrapper=dict):
    """
    Loads ACF content into a Python object.
    :param data: An UTF-8 encoded content of an ACF file.
    :param wrapper: A wrapping object for key-value pairs.
    :return: An Ordered Dictionary with ACF data.
    """
    if not isinstance(data, str):
        raise TypeError('can only load a str as an ACF but got ' + type(data).__name__)

    parsed = wrapper()
    current_section = parsed
    sections = []

    lines = (line.strip() for line in data.splitlines())

    for line in lines:
        try:
            key, value = line.split(None, 1)
            key = key.replace('"', '').lstrip()
            value = value.replace('"', '').rstrip()
        except ValueError:
            if line == SECTION_START:
                # Initialize the last added section.
                current_section = _prepare_subsection(parsed, sections, wrapper)
            elif line == SECTION_END:
                # Remove the last section from the queue.
                sections.pop()
            else:
                # Add a new section to the queue.
                sections.append(line.replace('"', ''))
            continue

        current_section[key] = value

    return parsed


def load(fp, wrapper=dict):
    """
    Loads the contents of an ACF file into a Python object.
    :param fp: A file object.
    :param wrapper: A wrapping object for key-value pairs.
    :return: An Ordered Dictionary with ACF data.
    """
    return loads(fp.read(), wrapper=wrapper)


def dumps(obj):
    """
    Serializes a dictionary into ACF data.
    :param obj: A dictionary to serialize.
    :return: ACF data.
    """
    if not isinstance(obj, dict):
        raise TypeError('can only dump a dictionary as an ACF but got ' + type(obj).__name__)

    return '\n'.join(_dumps(obj, level=0)) + '\n'


def dump(obj, fp):
    """
    Serializes a dictionary into ACF data and writes it to a file.
    :param obj: A dictionary to serialize.
    :param fp: A file object.
    """
    fp.write(dumps(obj))


def _dumps(obj, level):
    """
    Does the actual serializing of data into an ACF format.
    :param obj: A dictionary to serialize.
    :param level: Nesting level.
    :return: A List of strings.
    """
    lines = []
    indent = '\t' * level

    for key, value in obj.items():
        if isinstance(value, dict):
            # [INDENT]"KEY"
            # [INDENT]{
            line = indent + '"{}"\n'.format(key) + indent + '{'
            lines.append(line)
            # Increase intendation of the nested dict
            lines.extend(_dumps(value, level + 1))
            # [INDENT]}
            lines.append(indent + '}')
        else:
            # [INDENT]"KEY"[TAB][TAB]"VALUE"
            lines.append(indent + '"{}"'.format(key) + '\t\t' + '"{}"'.format(value))

    return lines


def _prepare_subsection(data, sections, wrapper):
    """
    Creates a subsection ready to be filled.
    :param data: Semi-parsed dictionary.
    :param sections: A list of sections.
    :param wrapper: A wrapping object for key-value pairs.
    :return: A newly created subsection.
    """
    current = data
    for i in sections[:-1]:
        current = current[i]

    current[sections[-1]] = wrapper()
    return current[sections[-1]]
