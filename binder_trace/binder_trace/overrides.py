"""Parsing override functions."""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING

import binder_trace.constants
from binder_trace import loggers
from binder_trace.parseerror import ParseError

if TYPE_CHECKING:
    from binder_trace.parcel import ParcelParser
    from binder_trace.parsedParcel import Field

parsing_log = logging.getLogger(loggers.PARSING_LOG)

# This file is specific to an android version and should be updated for each one
# Eventually I'll check this ANDROID_VERSION against the one in the AOSP sources

ANDROID_VERSION = "android-11.0.0_r25"


def parcelableHasOverride(parcelType: str) -> bool:
    """Check if a given parcelable type has an override parsing function defined in this file.

    :param parcelType: The parcelable type
    :return: True if an override is defined, False otherwise.
    """
    overrides = [
        "android.net.Uri",
        "android.net.Uri$StringUri",
        "android.net.Uri$OpaqueUri",
        "android.net.Uri$HierarchicalUri",
        "android.content.IntentFilter",
        "android.content.ComponentName",
        "android.internal.app.procstats.ProcessStats",
        "android.view.AbsSavedState$1",
        "android.net.LinkProperties",
        "android.content.pm.TextUtils",
        "android.text.TextUtils",
        "CharSequence",
        "Rect",
        "android.graphics.Bitmap",
        "android.view.InputChannel",
        "android.content.pm.ParceledListSlice",
        "android.content.pm.ResolveInfo",
        "android.database.BulkCursorDescriptor",
        "android.content.ContentProviderOperation",
        "android.content.ContentProviderOperation$BackReference",
    ]

    return parcelType in overrides


def parcelableOverride(parcel: ParcelParser, parcelType: str, name: str, parent: Field) -> None:
    """Handle the parser override of a parcelable type.

    :param parcel: The ParcelParser
    :param parcelType: The parcelable type
    :param name: The name of the parcelable
    :param parent: The parent field to parse.
    :raises ParseError: raised on parsing error.
    """
    override_handlers = {
        "android.net.Uri": parseUri,
        "android.net.Uri$StringUri": parseStringUri,
        "android.net.Uri$OpaqueUri": parseOpaqueUri,
        "android.net.Uri$HierarchicalUri": parseHierarchicalUri,
        "android.content.IntentFilter": parseIntentFilter,
        "android.content.ComponentName": parseComponentName,
        "android.internal.app.procstats.ProcessStats": parseProcessStats,
        "android.net.LinkProperties": parseLinkProperties,
        "android.content.pm.TextUtils": parseCharSequence,
        "android.text.TextUtils": parseCharSequence,
        "CharSequence": parseCharSequence,
        "android.graphics.Bitmap": parseBitmap,
        "android.view.InputChannel": parseInputChannel,
        "android.content.pm.ParceledListSlice": parseParceledListSlice,
        "android.content.pm.ResolveInfo": parseResolveInfo,
        "android.database.BulkCursorDescriptor": parseBulkCursorDescriptor,
        "android.content.ContentProviderOperation": parseContentProviderOperation,
        "android.content.ContentProviderOperation$BackReference": parseBackReference,
    }
    if parcelType in override_handlers:
        parcel.parse_field(
            name,
            parcelType,
            functools.partial(override_handlers[parcelType], parcel),
            parent,
        )
    elif parcelType == "android.view.AbsSavedState$1":
        parseAbsSavedState(parcel, name, parent)
    elif parcelType == "Rect":
        # TODO: is this ever called? Why would the type be "Rect" not android.graphics.Rect
        parcel.readParcelable("android.graphics.Rect", parent)
    else:
        parsing_log.info("No override for " + parcelType)
        raise ParseError("No override for " + parcelType)


def parseUri(parcel: ParcelParser, parent: Field) -> None:  # noqa
    code_field = parcel.parse_field("code", "uint32", parcel.readUint32, parent)

    if code_field.content == binder_trace.constants.URI_NULL_TYPE_ID:
        # TODO: Should we be outputting something for the NULL URI or is type code enough?
        pass
    elif code_field.content == binder_trace.constants.URI_STRING_TYPE_ID:
        parseStringUri(parcel, parent)
    elif code_field.content == binder_trace.constants.URI_OPAQUE_TYPE_ID:
        parseOpaqueUri(parcel, parent)
    elif code_field.content == binder_trace.constants.URI_HIERARCHICAL_TYPE_ID:
        parseHierarchicalUri(parcel, parent)
    else:
        raise ParseError(f"Unknown URI type: {code_field.content}")


def parseHierarchicalUri(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("scheme", "string", parcel.readString8, parent)
    parcel.parse_field("authority encoding", "string", parcel.readInt32, parent)
    parcel.parse_field("authority", "string", parcel.readString8, parent)
    parcel.parse_field("path encoding", "string", parcel.readInt32, parent)
    parcel.parse_field("path", "string", parcel.readString8, parent)
    parcel.parse_field("query encoding", "string", parcel.readInt32, parent)
    parcel.parse_field("query", "string", parcel.readString8, parent)
    parcel.parse_field("fragment encoding", "string", parcel.readInt32, parent)
    parcel.parse_field("fragment", "string", parcel.readString8, parent)


def parseOpaqueUri(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("scheme", "string", parcel.readString8, parent)
    parcel.parse_field("ssp encoding", "int32", parcel.readInt32, parent)
    parcel.parse_field("ssp", "string", parcel.readString8, parent)
    parcel.parse_field("fragment encoding", "int32", parcel.readInt32, parent)
    parcel.parse_field("fragment", "string", parcel.readString8, parent)


def parseStringUri(parcel: ParcelParser, parent: Field) -> None:  # noqa
    if parcel.android_version > 9:
        parcel.parse_field("uriString", "string", parcel.readString8, parent)
    else:
        parcel.parse_field("uriString", "string", parcel.readString16, parent)


def parseIntentFilter(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("mActions", "", parcel.readString16Vector, parent)

    category_nullcheck = parcel.parse_field("mCategories-nullcheck", "", parcel.readInt32, parent)
    if category_nullcheck.content:
        parcel.parse_field("mCategories", "", parcel.readString16Vector, parent)

    scheme_nullcheck = parcel.parse_field("mDataSchemes-nullcheck", "", parcel.readInt32, parent)
    if scheme_nullcheck.content:
        parcel.parse_field("mDataSchemes", "", parcel.readString16Vector, parent)

    static_types_nulllcheck = parcel.parse_field("mStaticDataTypes-nullcheck", "", parcel.readInt32, parent)
    if static_types_nulllcheck.content:
        parcel.parse_field("mStaticDataTypes", "", parcel.readString16Vector, parent)

    types_nullcheck = parcel.parse_field("mDataTypes-nullcheck", "", parcel.readInt32, parent)
    if types_nullcheck.content:
        parcel.parse_field("mDataTypes", "", parcel.readString16Vector, parent)

    group_nullcheck = parcel.parse_field("mMimeGroups-nullcheck", "", parcel.readInt32, parent)
    if group_nullcheck.content:
        parcel.parse_field("mMimeGroups", "", parcel.readString16Vector, parent)

    parcel.parse_field(
        "mDataSchemeSpecificParts",
        "",
        functools.partial(parcel.readParcelableVectorWithoutNullChecks, "PatternMatcher"),
        parent,
    )
    parcel.parse_field(
        "mDataAuthorities",
        "",
        functools.partial(parcel.readParcelableVectorWithoutNullChecks, "AuthorityEntry"),
        parent,
    )
    parcel.parse_field(
        "mDataPaths",
        "",
        functools.partial(parcel.readParcelableVectorWithoutNullChecks, "PatternMatcher"),
        parent,
    )

    parcel.parse_field("mPriority", "int32", parcel.readInt32, parent)
    parcel.parse_field("mHasStaticPartialTypes", "int32", parcel.readInt32, parent)
    parcel.parse_field("mHasDynamicPartialTypes", "int32", parcel.readInt32, parent)
    parcel.parse_field("setAutoVerify", "int32", parcel.readInt32, parent)
    parcel.parse_field("setVisibilityToInstantApp", "int32", parcel.readInt32, parent)
    parcel.parse_field("mOrder", "int32", parcel.readInt32, parent)


def parseComponentName(parcel: ParcelParser, parent: Field) -> None:  # noqa
    package = parcel.parse_field("mPackage", "string", parcel.readString16, parent)
    if package.content[0].content != -1:
        parcel.parse_field("mClass", "string", parcel.readString16, parent)


def parseProcessStats(parcel: ParcelParser, parent: Field) -> None:  # noqa
    # TODO: Add support for processing stats
    parsing_log.debug("Parsing unsupported type Process Stats")


def parseAbsSavedState(parcel: ParcelParser, name: str, parent: Field) -> None:  # noqa
    parcel.parse_field(
        name,
        "AbsSavedState",
        functools.partial(parcel.readParcelable, "__dynamic"),
        parent,
    )


def parseAddressList(parcel: ParcelParser, name: str, parent: Field) -> None:  # noqa
    count_field = parcel.parse_field("count", "int32", parcel.readInt32, parent)

    if not isinstance(count_field.content, int):
        raise ParseError("Expected integer size field")

    for i in range(count_field.content):
        parcel.parse_field("", "Address", functools.partial(readAddress, parcel), parent)


def readAddress(parcel: ParcelParser, parent: Field) -> None:  # noqa
    addr_field = parcel.parse_field("addr", "ByteVector", parcel.readByteVector, parent)

    if len(addr_field.content) == 16:
        parcel.parse_field("scopeId", "int32", parcel.readInt32, parent)


def parseLinkProperties(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("iface", "string", parcel.readString16, parent)

    parcel.parse_field(
        "linkAddresses",
        "",
        functools.partial(parcel.readParcelableVectorWithoutNullChecks, "__dynamic"),
        parent,
    )

    parcel.parse_field("DnsServers", "", parseAddressList, parent)
    parcel.parse_field("ValidatedPrivateDnsServer", parseAddressList, parent)

    parcel.parse_field("setUsePrivateDns", "bool", parcel.readBool, parent)
    parcel.parse_field("setPrivateDnsServerName", "string", parcel.readString16, parent)

    parcel.parse_field("PcscfServer", "", parseAddressList, parent)

    parcel.parse_field("setDomains", "string", parcel.readString16, parent)

    parcel.parse_field(
        "setDhcpServerAddress",
        "Address",
        functools.partial(readAddress, parcel),
        parent,
    )
    parcel.parse_field("setMtu", "int32", parcel.readInt32, parent)
    parcel.parse_field("setTcpBufferSizes", "string", parcel.readString16, parent)

    parcel.parse_field(
        "Routes",
        "",
        functools.partial(parcel.readParcelableVectorWithoutNullChecks, "__dynamic"),
        parent,
    )

    null_check_field = parcel.parse_field("HttpProxy-nullcheck", "", parcel.readBool, parent)
    if null_check_field.content:
        parcel.parse_field(
            "HttpProxy-nullcheck",
            "",
            functools.partial(parcel.readParcelable, "__dynamic"),
            parent,
        )

    parcel.parse_field(
        "setNat64Prefix",
        "",
        functools.partial(parcel.readParcelable, "__dynamic"),
        parent,
    )

    parcel.parse_field("stackedLinks", "List<LinkProperties>", parcel.readList, parent)
    parcel.parse_field("setWakeOnLanSupported", "bool", parcel.readBool, parent)

    parcel.parse_field(
        "setCaptivePortalApiUrl",
        "",
        functools.partial(parcel.readParcelable, "__dynamic"),
        parent,
    )

    parcel.parse_field(
        "setCaptivePortalData",
        "",
        functools.partial(parcel.readParcelable, "__dynamic"),
        parent,
    )


def parseCharSequence(parcel: ParcelParser, parent: Field) -> None:  # noqa
    span_names = {
        binder_trace.constants.SpanType.ALIGNMENT_SPAN: "AlignmentSpan",
        binder_trace.constants.SpanType.FOREGROUND_COLOR_SPAN: "ForegroundColorSpan",
        binder_trace.constants.SpanType.RELATIVE_SIZE_SPAN: "RelativeSizeSpan",
        binder_trace.constants.SpanType.SCALE_X_SPAN: "ScaleXSpan",
        binder_trace.constants.SpanType.STRIKETHROUGH_SPAN: "StrikethroughSpan",
        binder_trace.constants.SpanType.UNDERLINE_SPAN: "UnderlineSpan",
        binder_trace.constants.SpanType.STYLE_SPAN: "StyleSpan",
        binder_trace.constants.SpanType.BULLET_SPAN: "BulletSpan",
        binder_trace.constants.SpanType.QUOTE_SPAN: "QuoteSpan",
        binder_trace.constants.SpanType.LEADING_MARGIN_SPAN: "LeadingMarginSpan",
        binder_trace.constants.SpanType.URL_SPAN: "URLSpan",
        binder_trace.constants.SpanType.BACKGROUND_COLOR_SPAN: "BackgroundColorSpan",
        binder_trace.constants.SpanType.TYPEFACE_SPAN: "TypefaceSpan",
        binder_trace.constants.SpanType.SUPERSCRIPT_SPAN: "SuperscriptSpan",
        binder_trace.constants.SpanType.SUBSCRIPT_SPAN: "SubscriptSpan",
        binder_trace.constants.SpanType.ABSOLUTE_SIZE_SPAN: "AbsoluteSizeSpan",
        binder_trace.constants.SpanType.TEXT_APPEARANCE_SPAN: "TextAppearanceSpan",
        binder_trace.constants.SpanType.ANNOTATION: "Annotation",
        binder_trace.constants.SpanType.SUGGESTION_SPAN: "SuggestionSpan",
        binder_trace.constants.SpanType.SPELL_CHECK_SPAN: "SpellCheckSpan",
        binder_trace.constants.SpanType.SUGGESTION_RANGE_SPAN: "SuggestionRangeSpan",
        binder_trace.constants.SpanType.EASY_EDIT_SPAN: "EasyEditSpan",
        binder_trace.constants.SpanType.LOCALE_SPAN: "LocaleSpan",
        binder_trace.constants.SpanType.TTS_SPAN: "TtsSpan",
        binder_trace.constants.SpanType.ACCESSIBILITY_CLICKABLE_SPAN: "AccessibilityClickableSpan",
        binder_trace.constants.SpanType.ACCESSIBILITY_URL_SPAN: "AccessibilityURLSpan",
        binder_trace.constants.SpanType.LINE_BACKGROUND_SPAN: "LineBackgroundSpan",
        binder_trace.constants.SpanType.LINE_HEIGHT_SPAN: "LineHeightSpan",
        binder_trace.constants.SpanType.ACCESSIBILITY_REPLACEMENT_SPAN: "AccessibilityReplacementSpan",
    }

    spanned_string_type_field = parcel.parse_field("kind", "int32", parcel.readInt32, parent)
    string_field = parcel.parse_field("string", "string", parcel.readString8, parent)

    if string_field.content and spanned_string_type_field.content != 1:
        spanned_string_type_field = parcel.parse_field("kind", "int32", parcel.readInt32, parent)
        while spanned_string_type_field.content:
            if not isinstance(spanned_string_type_field.content, int):
                raise ParseError("Expected integer CharSequence kind type")

            span_type_name = span_names.get(spanned_string_type_field.content)

            parcel.parse_field(
                "span",
                span_type_name,
                functools.partial(parse_span, parcel, spanned_string_type_field.content),
                parent,
            )

            spanned_string_type_field = parcel.parse_field("kind", "int32", parcel.readInt32, parent)


def readSpan(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("spanStart", "int32", parcel.readInt32, parent)
    parcel.parse_field("spanEnd", "int32", parcel.readInt32, parent)
    parcel.parse_field("spanFlags", "int32", parcel.readInt32, parent)


def parse_span(parcel: ParcelParser, kind: int, parent: Field) -> None:  # noqa
    # TODO: Need to add the non-structural grouping fields
    if kind == binder_trace.constants.SpanType.ALIGNMENT_SPAN:
        parcel.parse_field("mAlignment", "string", parcel.readString16, parent)

    elif kind == binder_trace.constants.SpanType.FOREGROUND_COLOR_SPAN:
        parcel.parse_field("mColor", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.RELATIVE_SIZE_SPAN:
        parcel.parse_field("mProportion", "float", parcel.readFloat, parent)

    elif kind == binder_trace.constants.SpanType.SCALE_X_SPAN:
        parcel.parse_field("mProportion", "float", parcel.readFloat, parent)

    elif kind == binder_trace.constants.SpanType.STYLE_SPAN:
        parcel.parse_field("mStyle", "int32", parcel.readInt32, parent)
        parcel.parse_field("mFontWeightAdjustment", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.BULLET_SPAN:
        parcel.parse_field("mGapWidth", "int32", parcel.readInt32, parent)
        parcel.parse_field("mWantColor", "bool", parcel.readBool, parent)
        parcel.parse_field("mColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mBulletRadius", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.QUOTE_SPAN:
        parcel.parse_field("mColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mStripeWidth", "int32", parcel.readInt32, parent)
        parcel.parse_field("mGapWidth", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.LEADING_MARGIN_SPAN:
        parcel.parse_field("mFirst", "int32", parcel.readInt32, parent)
        parcel.parse_field("mRest", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.URL_SPAN:
        parcel.parse_field("mURL", "string", parcel.readString16, parent)

    elif kind == binder_trace.constants.SpanType.BACKGROUND_COLOR_SPAN:
        parcel.parse_field("mColor", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.TYPEFACE_SPAN:
        parcel.parse_field("mFamily", "int32", parcel.readString16, parent)
        parcel.parse_field("typefacePid", "int32", parcel.readInt32, parent)
        parcel.parse_field("typefaceId", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.ABSOLUTE_SIZE_SPAN:
        parcel.parse_field("mSize", "int32", parcel.readInt32, parent)
        parcel.parse_field("mDip", "int32", parcel.readBool, parent)

    elif kind == binder_trace.constants.SpanType.TEXT_APPEARANCE_SPAN:
        parcel.parse_field("mFamilyName", "string", parcel.readString16, parent)
        parcel.parse_field("mStyle", "int32", parcel.readInt32, parent)
        parcel.parse_field("mTextSize", "int32", parcel.readInt32, parent)

        color_nullcheck_field = parcel.parse_field("mTextColor-nullcheck", "int32", parcel.readInt32, parent)
        if color_nullcheck_field.content:
            parcel.parse_field(
                "mTextColor",
                "android.content.res.ColorStateList",
                functools.partial(parcel.readParcelable, "android.content.res.ColorStateList"),
                parent,
            )

        colorlink_nullcheck_field = parcel.parse_field("mTextColorLink-nullcheck", "int32", parcel.readInt32, parent)
        if colorlink_nullcheck_field.content:
            parcel.parse_field(
                "mTextColorLink",
                "android.content.res.ColorStateList",
                functools.partial(parcel.readParcelable, "android.content.res.ColorStateList"),
                parent,
            )

        parcel.parse_field("typefacePid", "int32", parcel.readInt32, parent)
        parcel.parse_field("typefaceId", "int32", parcel.readInt32, parent)
        parcel.parse_field("mTextFontWeight", "int32", parcel.readInt32, parent)
        parcel.parse_field(
            "mTextLocales",
            "",
            functools.partial(parcel.readParcelable, "__dynamic"),
            parent,
        )
        parcel.parse_field("mShadowRadius", "float", parcel.readFloat, parent)
        parcel.parse_field("mShadowDx", "float", parcel.readFloat, parent)
        parcel.parse_field("mShadowDy", "float", parcel.readFloat, parent)
        parcel.parse_field("mShadowColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mHasElegantTextHeight", "bool", parcel.readBool, parent)
        parcel.parse_field("mElegantTextHeight", "bool", parcel.readBool, parent)
        parcel.parse_field("mHasLetterSpacing", "bool", parcel.readBool, parent)
        parcel.parse_field("mLetterSpacing", "float", parcel.readFloat, parent)
        parcel.parse_field("mFontFeatureSettings", "string", parcel.readString16, parent)
        parcel.parse_field("mFontVariationSettings", "string", parcel.readString16, parent)

    elif kind == binder_trace.constants.SpanType.ANNOTATION:
        parcel.parse_field("mKey", "string", parcel.readString16, parent)
        parcel.parse_field("mValue", "string", parcel.readString16, parent)

    elif kind == binder_trace.constants.SpanType.SUGGESTION_SPAN:
        parcel.parse_field("mSuggestions", "string[]", parcel.readString16Vector, parent)
        parcel.parse_field("mFlags", "int32", parcel.readInt32, parent)
        parcel.parse_field("mLocaleStringForCompatibility", "string", parcel.readString16, parent)
        parcel.parse_field("mLanguageTag", "string", parcel.readString16, parent)
        parcel.parse_field("mHashCode", "int32", parcel.readInt32, parent)
        parcel.parse_field("mEasyCorrectUnderlineColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mEasyCorrectUnderlineThickness", "float", parcel.readFloat, parent)
        parcel.parse_field("mMisspelledUnderlineColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mMisspelledUnderlineThickness", "float", parcel.readFloat, parent)
        parcel.parse_field("mAutoCorrectionUnderlineColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mAutoCorrectionUnderlineThickness", "float", parcel.readFloat, parent)
        parcel.parse_field("mGrammarErrorUnderlineColor", "int32", parcel.readInt32, parent)
        parcel.parse_field("mGrammarErrorUnderlineThickness", "float", parcel.readFloat, parent)

    elif kind == binder_trace.constants.SpanType.SPELL_CHECK_SPAN:
        parcel.parse_field("mSpellCheckInProgress", "bool", parcel.readBool, parent)

    elif kind == binder_trace.constants.SpanType.SUGGESTION_RANGE_SPAN:
        parcel.parse_field("mBackgroundColor", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.EASY_EDIT_SPAN:
        parcel.parse_field(
            "mPendingIntent",
            "",
            functools.partial(parcel.readParcelable, "__dynamic"),
            parent,
        )
        parcel.parse_field("mDeleteEnabled", "int32", parcel.readByte, parent)

    elif kind == binder_trace.constants.SpanType.LOCALE_SPAN:
        parcel.parse_field(
            "mLocales",
            "",
            functools.partial(parcel.readParcelable, "android.os.LocaleList"),
            parent,
        )

    elif kind == binder_trace.constants.SpanType.TTS_SPAN:
        parcel.parse_field("mType", "string", parcel.readString16, parent)
        parcel.parse_field("mArgs", "bundle", parcel.readBundle, parent)

    elif kind == binder_trace.constants.SpanType.ACCESSIBILITY_CLICKABLE_SPAN:
        parcel.parse_field("mOriginalClickableSpanId", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.ACCESSIBILITY_URL_SPAN:
        parcel.parse_field("mURL", "string", parcel.readString16, parent)
        parcel.parse_field("mOriginalClickableSpanId", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.LINE_BACKGROUND_SPAN:
        parcel.parse_field("mColor", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.LINE_HEIGHT_SPAN:
        parcel.parse_field("mHeight", "int32", parcel.readInt32, parent)

    elif kind == binder_trace.constants.SpanType.ACCESSIBILITY_REPLACEMENT_SPAN:
        parcel.parse_field(
            "contentDescription",
            "CharSequence",
            functools.partial(parseCharSequence, parcel),
            parent,
        )

    elif kind == (
        binder_trace.constants.SpanType.SUPERSCRIPT_SPAN
        or binder_trace.constants.SpanType.SUBSCRIPT_SPAN
        or binder_trace.constants.SpanType.STRIKETHROUGH_SPAN
        or binder_trace.constants.SpanType.UNDERLINE_SPAN
    ):
        # These types just have the basic span fields.
        pass

    else:
        raise ParseError(f"Unknown span type '{kind}'")

    readSpan(parcel, parent)


# THIS CHANGED IN LATER ANDROID VERSIONS
def parseBitmap(parcel: ParcelParser, parent: Field) -> None:  # noqa
    def get_width_of_pixel_for_color_type(t) -> int:
        # Lines up with the color type definitions in asop:external/skqp/src/core/SkImageInfo.cpp
        if t == 0:
            return 0
        if t == 1 or t == 9:
            return 1
        if t == 2 or t == 3:
            return 2
        if t == 4 or t == 5 or t == 6 or t == 7 or t == 8:
            return 4
        if t == 10:
            return 8
        if t == 11 or t == 12:
            return 16
        raise ParseError(f"Unknown color type: {t}")

    def calc_byte_size(w, h, r, t) -> int:
        if h == 0:
            return 0
        return ((h - 1) * r) + (w * get_width_of_pixel_for_color_type(t))

    parcel.parse_field("isMutable", "int32", parcel.readInt32, parent)
    color_type_field = parcel.parse_field("colorType", "int32", parcel.readInt32, parent)

    parcel.parse_field("alphaType", "int32", parcel.readInt32, parent)
    parcel.parse_field("colorSpace", "byte[]", parcel.readByteVector, parent)

    width_field = parcel.parse_field("width", "int32", parcel.readInt32, parent)
    height_field = parcel.parse_field("height", "int32", parcel.readInt32, parent)
    row_bytes_field = parcel.parse_field("rowBytes", "int32", parcel.readInt32, parent)

    parcel.parse_field("density", "int32", parcel.readInt32, parent)

    blob_size = calc_byte_size(
        width_field.content,
        height_field.content,
        row_bytes_field.content,
        color_type_field.content,
    )

    parcel.parse_field("blob", "byte[]", functools.partial(parcel.readBlob, blob_size), parent)


def parseInputChannel(parcel: ParcelParser, parent: Field):  # noqa
    init_field = parcel.parse_field("isInitialized", "bool", parcel.readBool, parent)
    if init_field.content:
        parcel.parse_field("name", "string", parcel.readCString8, parent)
        parcel.parse_field("token", "string", parcel.readStrongBinder, parent)
        parcel.parse_field("mFd", "fd", parcel.readFileDescriptor, parent)


def parseResolveInfo(parcel: ParcelParser, parent: Field) -> None:  # noqa
    component_info_field = parcel.parse_field("componentInfoType", "int32", parcel.readInt32, parent)
    component_info_type = component_info_field.content
    if component_info_type == 1:
        parcel.parse_field(
            "activityInfo",
            "android.content.pm.ActivityInfo",
            functools.partial(parcel.readParcelable, "android.content.pm.ActivityInfo"),
            parent,
        )
    elif component_info_type == 2:
        parcel.parse_field(
            "serviceInfo",
            "android.content.pm.ServiceInfo",
            functools.partial(parcel.readParcelable, "android.content.pm.ServiceInfo"),
            parent,
        )
    elif component_info_type == 3:
        parcel.parse_field(
            "providerInfo",
            "android.content.pm.ProviderInfo",
            functools.partial(parcel.readParcelable, "android.content.pm.ProviderInfo"),
            parent,
        )

    filter_nullcheck_field = parcel.parse_field("filter-nullcheck", "int32", parcel.readInt32, parent)
    if filter_nullcheck_field.content != 0:
        parcel.parse_field(
            "filter",
            "IntentFilter",
            functools.partial(parcel.readParcelable, "IntentFilter"),
            parent,
        )

    parcel.parse_field("priority", "int32", parcel.readInt32, parent)
    parcel.parse_field("preferredorder", "int32", parcel.readInt32, parent)
    parcel.parse_field("match", "int32", parcel.readInt32, parent)
    parcel.parse_field("specificIndex", "int32", parcel.readInt32, parent)
    parcel.parse_field("labelRes", "int32", parcel.readInt32, parent)

    parcel.parse_field(
        "nonLocalizedLabel",
        "android.content.pm.TextUtils",
        functools.partial(parcel.readParcelable, "android.content.pm.TextUtils"),
        parent,
    )

    parcel.parse_field("icon", "int32", parcel.readInt32)
    parcel.parse_field("resolvePackageName", "string", parcel.readString8, parent)
    parcel.parse_field("targetUserId", "int32", parcel.readInt32, parent)
    parcel.parse_field("system", "bool", parcel.readBool, parent)
    parcel.parse_field("noResourceId", "bool", parcel.readBool, parent)
    parcel.parse_field("iconResourceId", "int32", parcel.readInt32, parent)
    parcel.parse_field("handleAllWebDataURI", "bool", parcel.readBool, parent)
    parcel.parse_field("isInstantAppAvailable", "bool", parcel.readBool, parent)


def parseParceledListSlice(parcel: ParcelParser, parent: Field) -> None:  # noqa
    count_field = parcel.parse_field("N", "int32", parcel.readInt32, parent)

    if not isinstance(count_field.content, int):
        raise ParseError("Expected integer field")

    count = count_field.content
    if count != 0:
        item_type_field = parcel.parse_field("listType", "string", parcel.readString16, parent)
        # Get the value out of the string type
        item_type = item_type_field.content[1].content

        for _ in range(count):
            item_nullcheck_field = parcel.parse_field("item-nullcheck", "int32", parcel.readInt32, parent)
            if item_nullcheck_field.content:  # This is a check to see if parcelable value follows
                parcel.parse_field("", "", functools.partial(parcel.readParcelable, item_type), parent)
        else:
            parcel.parse_field("<more elements>", "StrongBinder", parcel.readStrongBinder, parent)


def parseBulkCursorDescriptor(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("cursor", "StrongBinder", parcel.readStrongBinder, parent)
    parcel.parse_field("columnNames", "string[]", parcel.readString16Vector, parent)
    parcel.parse_field("wantsAllOnMoveCalls", "bool", parcel.readBool, parent)
    parcel.parse_field("count", "int32", parcel.readInt32, parent)
    window_nullcheck_field = parcel.parse_field("window-nullcheck", "int32", parcel.readInt32, parent)

    if window_nullcheck_field.content:
        parcel.parse_field(
            "window-nullcheck",
            "android.database.CursorWindow",
            functools.partial(parcel.readParcelable, "android.database.CursorWindow"),
            parent,
        )


def parseContentProviderOperation(parcel: ParcelParser, parent: Field):  # noqa
    parcel.parse_field("mType", "int32", parcel.readInt32, parent)
    parcel.parse_field(
        "mUri",
        "android.net.Uri",
        functools.partial(parcel.readParcelable, "android.net.Uri"),
        parent,
    )

    method_present_field = parcel.parse_field("mMethodPresent", "int32", parcel.readInt32, parent)
    if method_present_field.content:
        parcel.parse_field("mMethod", "string", parcel.readString8, parent)

    arg_present_field = parcel.parse_field("mArgPresent", "int32", parcel.readInt32, parent)
    if arg_present_field.content:
        parcel.parse_field("mArg", "string", parcel.readString8, parent)

    values_size_field = parcel.parse_field("valuesSize", "int32", parcel.readInt32, parent)
    if values_size_field.content != -1:
        parcel.parse_field("mValues", "ArrayMap", parcel.readArrayMap, parent)

    extras_size_field = parcel.parse_field("extrasSize", "int32", parcel.readInt32, parent)
    if extras_size_field.content != -1:
        parcel.parse_field("mExtras", "ArrayMap", parcel.readArrayMap, parent)

    selection_present_field = parcel.parse_field("mSelectionPresent", "int32", parcel.readInt32, parent)
    if selection_present_field.content:
        parcel.parse_field("mSelection", "string", parcel.readString8, parent)

    parcel.parse_field("mSelectionArgs", "SparseArray", parcel.readSparseArray, parent)

    count_present_field = parcel.parse_field("mExpectedCountPresent", "int32", parcel.readInt32, parent)
    if count_present_field.content:
        parcel.parse_field("mExpectedCount", "int32", parcel.readInt32, parent)

    parcel.parse_field("mYieldAllowed", "bool", parcel.readBool, parent)
    parcel.parse_field("mExceptionAllowed", "bool", parcel.readBool, parent)


def parseBackReference(parcel: ParcelParser, parent: Field) -> None:  # noqa
    parcel.parse_field("fromIndex", "int32", parcel.readInt32, parent)
    key_present_field = parcel.parse_field("fromKeyPresent", "int32", parcel.readInt32, parent)

    if key_present_field.content != 0:
        parcel.parse_field("fromKey", "string", parcel.readString8, parent)
