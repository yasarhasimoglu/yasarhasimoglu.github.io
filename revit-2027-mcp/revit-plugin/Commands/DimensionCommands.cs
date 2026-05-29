using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>
    /// Dış ölçüler oluşturur: mevcut aksları referans alarak bina dışına
    /// zincir (ara) ölçü ve toplam (genel) ölçü ekler. Aktif plan görünümünde çalışır.
    /// </summary>
    public static class DimensionCommands
    {
        public static object DimensionExterior(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;
            View view = ScaleStandardCommands.ResolveView(doc,
                app, Util.GetString(p, "view", null));

            if (!(view is ViewPlan))
                throw new InvalidOperationException("Dış ölçü için aktif görünüm bir plan olmalı.");

            double offset = Util.MmToFt(Util.GetDouble(p, "offset_mm", 1500));
            bool overall = Util.GetBool(p, "overall", true);

            var grids = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Grid)).Cast<Grid>()
                .Where(g => g.Curve is Line).ToList();

            if (grids.Count < 2)
                throw new InvalidOperationException("Ölçü için görünümde en az 2 aks gerekli.");

            var vertical = new List<Grid>();   // Y boyunca uzanan akslar (X'te konumlanır)
            var horizontal = new List<Grid>(); // X boyunca uzanan akslar (Y'de konumlanır)
            foreach (var g in grids)
            {
                XYZ dir = ((Line)g.Curve).Direction;
                if (Math.Abs(dir.Y) > Math.Abs(dir.X)) vertical.Add(g);
                else horizontal.Add(g);
            }

            // Modelin sınır kutusu (ölçü çizgisini dışarı koymak için).
            BoundingBoxXYZ bb = GridBounds(grids);
            var dims = new List<object>();

            using (var t = new Transaction(doc, "Dış ölçüler"))
            {
                t.Start();

                if (vertical.Count >= 2)
                {
                    vertical = vertical.OrderBy(g => ((Line)g.Curve).Origin.X).ToList();
                    double yLine = bb.Max.Y + offset;
                    dims.AddRange(MakeAxisDimensions(doc, view, vertical, isVertical: true,
                        linePos: yLine, overall, offset));
                }

                if (horizontal.Count >= 2)
                {
                    horizontal = horizontal.OrderBy(g => ((Line)g.Curve).Origin.Y).ToList();
                    double xLine = bb.Min.X - offset;
                    dims.AddRange(MakeAxisDimensions(doc, view, horizontal, isVertical: false,
                        linePos: xLine, overall, offset));
                }

                t.Commit();
            }

            return new { created_count = dims.Count, dimensions = dims };
        }

        private static IEnumerable<object> MakeAxisDimensions(Document doc, View view,
            List<Grid> ordered, bool isVertical, double linePos, bool overall, double offset)
        {
            var results = new List<object>();

            // Zincir (ara) ölçü: tüm aksları tek referans dizisine koy.
            var chain = new ReferenceArray();
            foreach (var g in ordered) chain.Append(new Reference(g));

            Line chainLine = isVertical
                ? Line.CreateBound(
                    new XYZ(((Line)ordered.First().Curve).Origin.X, linePos, 0),
                    new XYZ(((Line)ordered.Last().Curve).Origin.X, linePos, 0))
                : Line.CreateBound(
                    new XYZ(linePos, ((Line)ordered.First().Curve).Origin.Y, 0),
                    new XYZ(linePos, ((Line)ordered.Last().Curve).Origin.Y, 0));

            Dimension chainDim = doc.Create.NewDimension(view, chainLine, chain);
            results.Add(new { id = chainDim.Id.Value, kind = "chain",
                axis = isVertical ? "vertical" : "horizontal", segments = ordered.Count - 1 });

            // Genel (toplam) ölçü: yalnızca ilk ve son aks, biraz daha dışarıda.
            if (overall && ordered.Count > 2)
            {
                double pos2 = isVertical ? linePos + offset : linePos - offset;
                var ends = new ReferenceArray();
                ends.Append(new Reference(ordered.First()));
                ends.Append(new Reference(ordered.Last()));

                Line overallLine = isVertical
                    ? Line.CreateBound(
                        new XYZ(((Line)ordered.First().Curve).Origin.X, pos2, 0),
                        new XYZ(((Line)ordered.Last().Curve).Origin.X, pos2, 0))
                    : Line.CreateBound(
                        new XYZ(pos2, ((Line)ordered.First().Curve).Origin.Y, 0),
                        new XYZ(pos2, ((Line)ordered.Last().Curve).Origin.Y, 0));

                Dimension overallDim = doc.Create.NewDimension(view, overallLine, ends);
                results.Add(new { id = overallDim.Id.Value, kind = "overall",
                    axis = isVertical ? "vertical" : "horizontal" });
            }

            return results;
        }

        private static BoundingBoxXYZ GridBounds(List<Grid> grids)
        {
            double minX = double.MaxValue, minY = double.MaxValue;
            double maxX = double.MinValue, maxY = double.MinValue;
            foreach (var g in grids)
            {
                var ln = (Line)g.Curve;
                foreach (var pt in new[] { ln.GetEndPoint(0), ln.GetEndPoint(1) })
                {
                    minX = Math.Min(minX, pt.X); maxX = Math.Max(maxX, pt.X);
                    minY = Math.Min(minY, pt.Y); maxY = Math.Max(maxY, pt.Y);
                }
            }
            return new BoundingBoxXYZ { Min = new XYZ(minX, minY, 0), Max = new XYZ(maxX, maxY, 0) };
        }
    }
}
