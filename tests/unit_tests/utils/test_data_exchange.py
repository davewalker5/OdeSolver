import pytest
import os
import json
import xml.etree.ElementTree as etree
from ode_solver import write_csv, write_json, write_xml


def get_test_file_path(extension):
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_file_path = os.path.join(tests_folder, "data", f"output.{extension}")

    if os.path.exists(test_file_path):
        os.unlink(test_file_path)

    return test_file_path


@pytest.fixture()
def csv_output_file():
    return get_test_file_path("csv")


@pytest.fixture()
def json_output_file():
    return get_test_file_path("json")


@pytest.fixture()
def xml_output_file():
    return get_test_file_path("xml")


@pytest.fixture()
def example_history():
    return [
        {
            "method": "Euler",
            "step": 0,
            "t": "0.0",
            "y": "0.5"
        },
        {
            "method": "Euler",
            "step": 1,
            "t": "0.5",
            "y": "1.25"
        }
    ]


def test_write_csv(example_history, csv_output_file):
    write_csv(example_history, csv_output_file)

    with open(csv_output_file, mode="rt", encoding="utf-8") as csv_f:
        lines = csv_f.readlines()
    os.unlink(csv_output_file)

    expected_headers = ",".join(list(example_history[0].keys()))
    assert expected_headers == lines[0].replace("\n", "")

    for i, point in enumerate(example_history):
        assert ",".join([str(v) for v in point.values()]) == lines[i + 1].replace("\n", "")


def test_write_json(example_history, json_output_file):
    write_json(example_history, json_output_file)

    with open(json_output_file, mode="rt", encoding="utf-8") as json_f:
        loaded_history = json.load(json_f)
    os.unlink(json_output_file)

    assert list == type(loaded_history)

    keys = list(example_history[0].keys())
    for i, point in enumerate(example_history):
        for key in keys:
            assert point[key] == loaded_history[i][key]


def test_write_xml(example_history, xml_output_file):
    write_xml(example_history, xml_output_file)

    with open(xml_output_file, mode="rt", encoding="utf-8") as xml_f:
        xml_string = xml_f.read()
    os.unlink(xml_output_file)

    tree = etree.ElementTree(etree.fromstring(xml_string))
    root = tree.getroot()
    points = root.findall(".//simulation/point")

    keys = list(example_history[0].keys())
    for i, point in enumerate(points):
        for key in keys:
            sub_element = point.findall(f".//{key}")[0]
            assert example_history[i][key] == sub_element.text
