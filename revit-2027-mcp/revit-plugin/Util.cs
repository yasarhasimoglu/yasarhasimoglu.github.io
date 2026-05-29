using System;
using System.Text.Json;
using Autodesk.Revit.DB;

namespace RevitMcpPlugin
{
    /// <summary>JSON parametre okuma ve birim dönüşümü yardımcıları.</summary>
    public static class Util
    {
        public static double GetDouble(JsonElement p, string name, double def)
        {
            if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty(name, out var v)
                && v.ValueKind == JsonValueKind.Number)
                return v.GetDouble();
            return def;
        }

        public static int GetInt(JsonElement p, string name, int def)
        {
            if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty(name, out var v)
                && v.ValueKind == JsonValueKind.Number)
                return v.GetInt32();
            return def;
        }

        public static string GetString(JsonElement p, string name, string def)
        {
            if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty(name, out var v)
                && v.ValueKind == JsonValueKind.String)
                return v.GetString();
            return def;
        }

        public static bool GetBool(JsonElement p, string name, bool def)
        {
            if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty(name, out var v)
                && (v.ValueKind == JsonValueKind.True || v.ValueKind == JsonValueKind.False))
                return v.GetBoolean();
            return def;
        }

        public static bool TryGetArray(JsonElement p, string name, out JsonElement arr)
        {
            arr = default;
            if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty(name, out var v)
                && v.ValueKind == JsonValueKind.Array)
            {
                arr = v;
                return true;
            }
            return false;
        }

        // --- Birim dönüşümleri (Revit içsel birimi = feet) ---

        public static double MmToFt(double mm) =>
            UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters);

        public static double MToFt(double m) =>
            UnitUtils.ConvertToInternalUnits(m, UnitTypeId.Meters);

        public static double FtToM(double ft) =>
            UnitUtils.ConvertFromInternalUnits(ft, UnitTypeId.Meters);

        public static double SqFtToSqM(double sqft) =>
            UnitUtils.ConvertFromInternalUnits(sqft, UnitTypeId.SquareMeters);

        public static double Round(double v, int digits = 2) => Math.Round(v, digits);
    }
}
