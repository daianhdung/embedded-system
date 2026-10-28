#pragma once
#if __has_include("pccc_build_identity.h")
#include "pccc_build_identity.h"
#else
#define PCCC_FIRMWARE_ID "HOST_UNSTAMPED"
#endif
inline const char* firmwareIdentity() { return PCCC_FIRMWARE_ID; }
