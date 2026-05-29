using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>
    /// Türkiye İmar Yönetmeliği'ne göre alan hesapları:
    ///  - Toplam (brüt) inşaat alanı: tüm katların alan toplamı.
    ///  - Emsal (KAKS) = emsale dahil inşaat alanı / parsel alanı.
    ///  - TAKS = taban alanı / parsel alanı.
    /// Alanlar modeldeki Mahaller (Rooms) üzerinden hesaplanır. Mahal alanı
    /// genelde net/aks-orta alandır; brüt için gross_factor ile çarpılabilir.
    /// </summary>
    public static class EmsalCommands
    {
        public static object CalculateTotalArea(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;
            double grossFactor = Util.GetDouble(p, "gross_factor", 1.0);

            var byLevel = AreaByLevel(doc);
            double totalNet = byLevel.Sum(l => l.area_m2);
            double totalGross = Util.Round(totalNet * grossFactor);

            return new
            {
                method = "Mahal (Room) alanları toplamı",
                gross_factor = grossFactor,
                level_count = byLevel.Count,
                levels = byLevel,
                total_net_m2 = Util.Round(totalNet),
                total_construction_area_m2 = totalGross
            };
        }

        public static object CalculateEmsal(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;

            double plotArea = Util.GetDouble(p, "plot_area_m2", 0);
            double grossFactor = Util.GetDouble(p, "gross_factor", 1.0);
            string footprintLevel = Util.GetString(p, "footprint_level", null);

            // Emsal harici sayılacak mahal adı anahtar kelimeleri (sığınak, otopark, vb.)
            var excludeKeywords = new List<string>();
            if (Util.TryGetArray(p, "exclude_keywords", out var arr))
                foreach (var e in arr.EnumerateArray())
                    if (e.ValueKind == JsonValueKind.String)
                        excludeKeywords.Add(e.GetString().ToLowerInvariant());

            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .Cast<Autodesk.Revit.DB.SpatialElement>()
                .Where(r => r.Area > 0)
                .ToList();

            double totalGross = 0, excludedArea = 0;
            var excludedDetail = new List<object>();
            var levelTotals = new Dictionary<string, double>();

            foreach (var r in rooms)
            {
                double m2 = Util.SqFtToSqM(r.Area) * grossFactor;
                totalGross += m2;
                string lvl = doc.GetElement(r.LevelId)?.Name ?? "—";
                levelTotals[lvl] = levelTotals.GetValueOrDefault(lvl) + m2;

                string nameLower = (r.Name ?? "").ToLowerInvariant();
                if (excludeKeywords.Any(k => nameLower.Contains(k)))
                {
                    excludedArea += m2;
                    excludedDetail.Add(new { room = r.Name,
                        level = lvl, area_m2 = Util.Round(m2) });
                }
            }

            double emsalArea = totalGross - excludedArea;

            // TAKS taban alanı: belirtilen kat ya da en alt kat.
            string groundLevel = footprintLevel;
            if (string.IsNullOrEmpty(groundLevel) && levelTotals.Count > 0)
            {
                var lowest = new FilteredElementCollector(doc).OfClass(typeof(Level))
                    .Cast<Level>().OrderBy(l => l.Elevation)
                    .FirstOrDefault(l => levelTotals.ContainsKey(l.Name));
                groundLevel = lowest?.Name;
            }
            double taksArea = groundLevel != null
                ? levelTotals.GetValueOrDefault(groundLevel) : 0;

            object emsal = plotArea > 0
                ? (object)Util.Round(emsalArea / plotArea, 4) : "parsel alanı gerekli";
            object taks = plotArea > 0
                ? (object)Util.Round(taksArea / plotArea, 4) : "parsel alanı gerekli";

            return new
            {
                plot_area_m2 = plotArea,
                gross_factor = grossFactor,
                total_construction_area_m2 = Util.Round(totalGross),
                excluded_area_m2 = Util.Round(excludedArea),
                exclude_keywords = excludeKeywords,
                excluded_rooms = excludedDetail,
                emsal_area_m2 = Util.Round(emsalArea),
                emsal_KAKS = emsal,
                footprint_level = groundLevel,
                taban_alani_m2 = Util.Round(taksArea),
                TAKS = taks,
                levels = levelTotals.Select(kv => new {
                    level = kv.Key, area_m2 = Util.Round(kv.Value) }).ToList(),
                note = "Brüt yaklaşımı mahal alanlarına dayanır; resmi hesap için " +
                       "duvar dış yüzüne göre kontrol önerilir."
            };
        }

        private static List<LevelArea> AreaByLevel(Document doc)
        {
            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .Cast<Autodesk.Revit.DB.SpatialElement>()
                .Where(r => r.Area > 0);

            var map = new Dictionary<string, double>();
            foreach (var r in rooms)
            {
                string lvl = doc.GetElement(r.LevelId)?.Name ?? "—";
                map[lvl] = map.GetValueOrDefault(lvl) + Util.SqFtToSqM(r.Area);
            }
            return map.Select(kv => new LevelArea {
                level = kv.Key, area_m2 = Util.Round(kv.Value) }).ToList();
        }

        private class LevelArea
        {
            public string level { get; set; }
            public double area_m2 { get; set; }
        }
    }
}
