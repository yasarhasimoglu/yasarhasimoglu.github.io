using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>
    /// Akslar (gridler) oluşturur. Düşey akslar harflerle (A, B, C…), yatay akslar
    /// rakamlarla (1, 2, 3…) adlandırılır. Aralıklar mm cinsinden verilir.
    /// </summary>
    public static class GridCommands
    {
        public static object CreateGrids(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;

            double originX = Util.MmToFt(Util.GetDouble(p, "origin_x_mm", 0));
            double originY = Util.MmToFt(Util.GetDouble(p, "origin_y_mm", 0));
            // Aks çizgilerinin model uzunluğu (taşma payı dahil).
            double margin = Util.MmToFt(Util.GetDouble(p, "margin_mm", 2000));

            var xSpacings = ReadSpacings(p, "x_spacings_mm"); // düşey aksların X aralıkları
            var ySpacings = ReadSpacings(p, "y_spacings_mm"); // yatay aksların Y aralıkları

            // Aks çizgi uzunlukları: tüm aks ağını saracak şekilde.
            double totalX = SumWithOrigin(xSpacings, originX);
            double totalY = SumWithOrigin(ySpacings, originY);
            double yMin = originY - margin;
            double yMax = totalY + margin;
            double xMin = originX - margin;
            double xMax = totalX + margin;

            var created = new List<object>();

            using (var t = new Transaction(doc, "Akslar oluştur"))
            {
                t.Start();

                // Düşey akslar (X boyunca konumlanır, Y boyunca uzanır) -> harf etiketi
                double x = originX;
                int letterIndex = 0;
                created.Add(MakeVerticalGrid(doc, x, yMin, yMax, Letter(letterIndex++)));
                foreach (double s in xSpacings)
                {
                    x += Util.MmToFt(s);
                    created.Add(MakeVerticalGrid(doc, x, yMin, yMax, Letter(letterIndex++)));
                }

                // Yatay akslar (Y boyunca konumlanır, X boyunca uzanır) -> rakam etiketi
                double y = originY;
                int num = 1;
                created.Add(MakeHorizontalGrid(doc, y, xMin, xMax, num++.ToString()));
                foreach (double s in ySpacings)
                {
                    y += Util.MmToFt(s);
                    created.Add(MakeHorizontalGrid(doc, y, xMin, xMax, num++.ToString()));
                }

                t.Commit();
            }

            return new { created_count = created.Count, grids = created };
        }

        private static object MakeVerticalGrid(Document doc, double x, double y0, double y1, string name)
        {
            Line line = Line.CreateBound(new XYZ(x, y0, 0), new XYZ(x, y1, 0));
            Grid g = Grid.Create(doc, line);
            TrySetName(g, name);
            return new { id = g.Id.Value, name = g.Name, axis = "vertical" };
        }

        private static object MakeHorizontalGrid(Document doc, double y, double x0, double x1, string name)
        {
            Line line = Line.CreateBound(new XYZ(x0, y, 0), new XYZ(x1, y, 0));
            Grid g = Grid.Create(doc, line);
            TrySetName(g, name);
            return new { id = g.Id.Value, name = g.Name, axis = "horizontal" };
        }

        private static void TrySetName(Grid g, string name)
        {
            try { g.Name = name; } catch { /* isim çakışırsa Revit'in verdiği ad kalır */ }
        }

        private static List<double> ReadSpacings(JsonElement p, string key)
        {
            var list = new List<double>();
            if (Util.TryGetArray(p, key, out var arr))
                foreach (var e in arr.EnumerateArray())
                    if (e.ValueKind == JsonValueKind.Number) list.Add(e.GetDouble());
            return list;
        }

        private static double SumWithOrigin(List<double> spacingsMm, double originFt)
        {
            double total = originFt;
            foreach (double s in spacingsMm) total += Util.MmToFt(s);
            return total;
        }

        private static string Letter(int index)
        {
            // 0->A, 25->Z, 26->AA ...
            string s = "";
            index++;
            while (index > 0)
            {
                index--;
                s = (char)('A' + index % 26) + s;
                index /= 26;
            }
            return s;
        }
    }
}
