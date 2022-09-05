import csv
import json
from ode_solver.utils.decimal_encoder import DecimalEncoder
from xml.etree.ElementTree import Element, fromstring, tostring
from xml.dom import minidom


def write_csv(history, filepath):
    """
    Write a run history to a CSV file

    :param history: List of dictionaries representing points in the solution
    :param filepath: Path to the output file
    """
    headers = list(history[0].keys())
    with open(filepath, mode="wt", encoding="utf-8", newline="") as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(history)


def write_json(history, filepath):
    """
    Write a run history to a JSON file

    :param history: List of dictionaries representing points in the solution
    :param filepath: Path to the output file
    """
    with open(filepath, mode="wt", encoding="utf-8") as json_f:
        json.dump(history, json_f, indent=4, cls=DecimalEncoder)


def point_to_xml_element(point, tag):
    """
    Convert a single point in a run history to an XML element

    :param point: Point to convert
    :param tag: XML tag name for the point
    :return: XML element representing the point
    """
    element = Element(tag)
    for key, value in point.items():
        child = Element(key)
        child.text = str(value)
        element.append(child)

    return element


def write_xml(history, filepath, root_tag="simulation", point_tag="point"):
    """
    Write a run history to an XML file

    :param history: List of dictionaries representing points in the solution
    :param filepath: Path to the output file
    """
    # Create an element tree from the list of points in the history
    root = fromstring(f"<{root_tag}/>")
    for point in history:
        point_element = point_to_xml_element(point, point_tag)
        root.append(point_element)

    # Convert the tree to an XML string and pretty-print it
    xml_string = tostring(root).decode(encoding="utf-8")
    xml_pretty = minidom.parseString(xml_string).toprettyxml(indent="    ")

    # Write the formatted XML string to the output file
    with open(filepath, mode="wt", encoding="utf-8") as xml_f:
        xml_f.write(xml_pretty)
