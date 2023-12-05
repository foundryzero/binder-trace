# noqa

# Due to time constraints, I was not able to finish this / make a nicer solution than this hacky override.
# It mirrors:
# https://cs.android.com/android/platform/superproject/+/android-11.0.0_r48:frameworks/base/core/java/android/content
#   /ContentProviderNative.java


from typing import Any, Dict


def queryTransaction1() -> Dict[Any, Any]:
    """queryTransaction1 override."""
    c: Dict[Any, Any] = {}
    c["code"] = 1
    c["in"] = []
    c["in"].append({"callingPkg": "readString16"})
    c["in"].append({"callingFeatureId": "readString16"})
    c["in"].append({"url": "readParcelable", "__parcelType": "android.net.Uri"})
    c["in"].append({"projection": "readString16Vector"})
    c["in"].append({"queryArgs": "readBundle"})
    c["in"].append({"observer": "readStrongBinder"})
    c["in"].append({"cancellactionSignal": "readStrongBinder"})
    c["out"] = []
    c["out"].append({"__exception": "readException"})
    c["out"].append({"nullcheck": "readInt32"})
    c["out"].append(
        {
            "__backreference": "nullcheck",
            "__conditional": [
                {
                    "__return": "readParcelable",
                    "__parcelType": "android.database.BulkCursorDescriptor",
                }
            ],
        }
    )
    c["name"] = "query"
    c["oneWay"] = False
    return c


def getTypeTransaction2() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 2
    c["in"] = []
    c["out"] = []
    c["name"] = "getType"
    c["oneWay"] = False
    return c


def insertTransaction3() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 3
    c["in"] = []
    c["out"] = []
    c["name"] = "insert"
    c["oneWay"] = False
    return c


def deleteTransaction4() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 4
    c["in"] = []
    c["out"] = []
    c["name"] = "delete"
    c["oneWay"] = False
    return c


def updateTransaction10() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 10
    c["in"] = []
    c["out"] = []
    c["name"] = "update"
    c["oneWay"] = False
    return c


def bulkInsertTransaction13() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 13
    c["in"] = []
    c["out"] = []
    c["name"] = "bulkInsert"
    c["oneWay"] = False
    return c


def openFileTransaction14() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 14
    c["in"] = []
    c["out"] = []
    c["name"] = "openFile"
    c["oneWay"] = False
    return c


def openAssetFileTransaction15() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 15
    c["in"] = []
    c["out"] = []
    c["name"] = "openAssetFile"
    c["oneWay"] = False
    return c


def applyBatchTransaction20() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 20
    c["in"] = []
    c["in"].append({"callingPkg": "readString16"})
    c["in"].append({"featureId": "readString16"})
    c["in"].append({"authority": "readString16"})
    c["in"].append({"numOperations": "readInt32"})
    c["in"].append(
        {
            "__backreference": "numOperations",
            "__repeated": [
                {
                    "operation": "readParcelable",
                    "__parcelType": "android.content.ContentProviderOperation",
                }
            ],
        }
    )

    c["out"] = []
    c["name"] = "applyBatch"
    c["oneWay"] = False
    return c


def callTransaction21() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 21
    c["in"] = []
    c["in"].append({"callingPkg": "readString16"})
    c["in"].append({"featureId": "readString16"})
    c["in"].append({"authority": "readString16"})
    c["in"].append({"method": "readString16"})
    c["in"].append({"stringArg": "readString16"})
    c["in"].append({"extras": "readBundle"})
    c["out"] = []
    c["out"].append({"__exception": "readException"})
    c["out"].append({"__return": "readBundle"})
    c["name"] = "call"
    c["oneWay"] = False

    return c


def getStreamTypesTransaction22() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 22
    c["in"] = []
    c["out"] = []
    c["name"] = "getStreamTypes"
    c["oneWay"] = False
    return c


def openTypedAssetFileTransaction23() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 23
    c["in"] = []
    c["out"] = []
    c["name"] = "openTypedAssetFile"
    c["oneWay"] = False
    return c


def createCancelationSignalTransaction24() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 24
    c["in"] = []
    c["out"] = []
    c["name"] = "createCancellationSignal"
    c["oneWay"] = False
    return c


def canonicalizeTransaction25() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 25
    c["in"] = []
    c["out"] = []
    c["name"] = "canonicalize"
    c["oneWay"] = False
    return c


def uncanonicalizeTransaction26() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 26
    c["in"] = []
    c["out"] = []
    c["name"] = "uncanonicalize"
    c["oneWay"] = False
    return c


def refreshTransaction27() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 27
    c["in"] = []
    c["out"] = []
    c["name"] = "refresh"
    c["oneWay"] = False
    return c


def checkUriPermissionTransaction28() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 28
    c["in"] = []
    c["out"] = []
    c["name"] = "checkUriPermission"
    c["oneWay"] = False
    return c


def asyncGetTypeTransaction29() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 29
    c["in"] = []
    c["out"] = []
    c["name"] = "getTypeAsync"
    c["oneWay"] = True
    return c


def asyncCanonicalizeTransaction30() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 30
    c["in"] = []
    c["out"] = []
    c["name"] = "canonicalizeAsync"
    c["oneWay"] = True
    return c


def asyncUncanonicalizeTransaction31() -> Dict[Any, Any]:  # noqa
    c: Dict[Any, Any] = {}
    c["code"] = 31
    c["in"] = []
    c["out"] = []
    c["name"] = "uncanonicalizeAsync"
    c["oneWay"] = True
    return c


def getIContentProviderInterface() -> Dict[Any, Any]:  # noqa
    interface: Dict[Any, Any] = {}
    interface["produced_on"] = ""
    interface["full_name"] = "android.content.IContentProvider"
    interface["name"] = "IContentProvider"
    interface["type"] = "Interface"

    calls = [
        queryTransaction1(),
        getTypeTransaction2(),
        insertTransaction3(),
        deleteTransaction4(),
        updateTransaction10(),
        bulkInsertTransaction13(),
        openFileTransaction14(),
        openAssetFileTransaction15(),
        applyBatchTransaction20(),
        callTransaction21(),
        getStreamTypesTransaction22(),
        openTypedAssetFileTransaction23(),
        createCancelationSignalTransaction24(),
        canonicalizeTransaction25(),
        uncanonicalizeTransaction26(),
        refreshTransaction27(),
        checkUriPermissionTransaction28(),
        asyncGetTypeTransaction29(),
        asyncCanonicalizeTransaction30(),
        asyncUncanonicalizeTransaction31(),
    ]

    interface["calls"] = calls

    return interface
