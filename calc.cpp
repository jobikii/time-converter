#include <cmath>
#include <cstdio>
#include <cstring>

#ifdef _WIN32
    #define EXPORT extern "C" __declspec(dllexport)
#else
    #define EXPORT extern "C"
#endif


double getUnitInSeconds(char unit) {
    switch (unit) {
        case 'S': return 1.0;
        case 'M': return 60.0;
        case 'H': return 3600.0;
        case 'D': return 86400.0;
        case 'W': return 604800.0;
        case 'O': return 2592000.0;
        case 'Y': return 31536000.0;
        default:  return -1.0;
    }
}


EXPORT int validateInput(double value, char unit) {
    if (value < 0.0 || std::isnan(value) || std::isinf(value)) {
        return -1;
    }
    if (getUnitInSeconds(unit) < 0.0) {
        return -2;
    }
    return 0;
}


EXPORT double convertTime(double value, char fromUnit, char toUnit) {
    if (validateInput(value, fromUnit) != 0) return -1.0;
    double toSec = getUnitInSeconds(toUnit);
    if (toSec < 0.0) return -2.0;
    double fromSec = getUnitInSeconds(fromUnit);
    return (value * fromSec) / toSec;
}


EXPORT int compareTime(double val1, char unit1, double val2, char unit2) {
    if (validateInput(val1, unit1) != 0 || validateInput(val2, unit2) != 0) {
        return -99;
    }

    double totalSec1 = val1 * getUnitInSeconds(unit1);
    double totalSec2 = val2 * getUnitInSeconds(unit2);

    const double EPSILON = 1e-9;
    if (std::fabs(totalSec1 - totalSec2) < EPSILON) {
        return 0;  // '='
    }
    return (totalSec1 > totalSec2) ? 1 : -1;
}

void sectoRecursive(long long S, char W, char* buffer, size_t maxLen) {
    long long c = 1;
    char next_W = ' ';

    switch (W) {
        case 'Y': c = 31536000; next_W = 'O'; break;
        case 'O': c = 2592000;  next_W = 'W'; break;
        case 'W': c = 604800;   next_W = 'D'; break;
        case 'D': c = 86400;    next_W = 'H'; break;
        case 'H': c = 3600;     next_W = 'M'; break;
        case 'M': c = 60;       next_W = 'S'; break;
        case 'S': c = 1;        next_W = ' '; break;
    }

    long long k = S / c;
    long long remainder = S % c;

    if (k > 0) {
        char temp[32];
        std::snprintf(temp, sizeof(temp), "%lld%c ", k, W);
        if (std::strlen(buffer) + std::strlen(temp) < maxLen) {
            std::strcat(buffer, temp);
        }
    }

    if (remainder > 0 && next_W != ' ') {
        sectoRecursive(remainder, next_W, buffer, maxLen);
    }
}

EXPORT void formatHumanReadable(double value, char unit, char* outBuffer, int maxLen) {
    if (outBuffer == nullptr || maxLen <= 0) return;
    outBuffer[0] = '\0';

    if (validateInput(value, unit) != 0) {
        std::snprintf(outBuffer, maxLen, "Error");
        return;
    }

    long long totalSeconds = static_cast<long long>(std::llround(value * getUnitInSeconds(unit)));
    if (totalSeconds == 0) {
        std::snprintf(outBuffer, maxLen, "0S");
        return;
    }

    sectoRecursive(totalSeconds, 'Y', outBuffer, static_cast<size_t>(maxLen));
}