# noqa
from typing import Any, Dict


def getCursorWindowTransaction1() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 1
    c["in"] = []
    c["out"] = []
    c["name"] = "getCursorWindow"
    c["oneWay"] = False
    return c


def deactivateTransaction2() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 2
    c["in"] = []
    c["out"] = []
    c["name"] = "deactivate"
    c["oneWay"] = False
    return c


def requeryTransaction3() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 3
    c["in"] = []
    c["out"] = []
    c["name"] = "requery"
    c["oneWay"] = False
    return c


def onMoveTransaction4() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 4
    c["in"] = []
    c["out"] = []
    c["name"] = "onMove"
    c["oneWay"] = False
    return c


def getExtrasTransaction5() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 5
    c["in"] = []
    c["out"] = []
    c["name"] = "getExtras"
    c["oneWay"] = False
    return c


def respondTransaction6() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 6
    c["in"] = []
    c["out"] = []
    c["name"] = "respond"
    c["oneWay"] = False
    return c


def closeTransaction7() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 7
    c["in"] = []
    c["out"] = []
    c["name"] = "close"
    c["oneWay"] = False
    return c


def getIBulkCursorInterface() -> Dict[Any, Any]:  # noqa
    interface: Dict[Any, Any] = {}
    interface["produced_on"] = ""
    interface["full_name"] = "android.database.IBulkCursor"
    interface["name"] = "IBulkCursor"
    interface["type"] = "Interface"

    calls = [
        getCursorWindowTransaction1(),
        deactivateTransaction2(),
        requeryTransaction3(),
        onMoveTransaction4(),
        getExtrasTransaction5(),
        respondTransaction6(),
        closeTransaction7(),
    ]

    interface["calls"] = calls

    return interface
