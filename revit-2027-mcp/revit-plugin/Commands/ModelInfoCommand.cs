using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>Açık model hakkında özet bilgi (katlar, mahaller, gridler, parsel).</summary>
    public static class ModelInfoCommand
    {
        public static object GetModelInfo(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level)).Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevation_m = Util.Round(Util.FtToM(l.Elevation), 3)
                }).ToList();

            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .Cast<SpatialElement>()
                .Where(r => r.Area > 0)
                .Select(r => new
                {
                    id = r.Id.Value,
                    name = r.Name,
                    number = (r as Room)?.Number,
                    level = doc.GetElement(r.LevelId)?.Name,
                    area_m2 = Util.Round(Util.SqFtToSqM(r.Area))
                }).ToList();

            int gridCount = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid)).GetElementIds().Count;

            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(View)).Cast<View>()
                .Where(v => !v.IsTemplate && v.CanBePrinted)
                .Select(v => new { id = v.Id.Value, name = v.Name, scale = v.Scale,
                    type = v.ViewType.ToString() })
                .ToList();

            return new
            {
                title = doc.Title,
                length_unit = "mm/m (içsel: ft)",
                level_count = levels.Count,
                levels,
                room_count = rooms.Count,
                rooms,
                grid_count = gridCount,
                views
            };
        }
    }
}
