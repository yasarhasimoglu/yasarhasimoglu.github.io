using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>
    /// Aktif görünümü 1/50 çizim standardına ayarlar: görünüm ölçeği 1:50,
    /// detay seviyesi Fine. Anotasyon (ölçü/etiket) boyutları Revit'te kâğıt
    /// boyutu olarak tanımlıdır; 1:50'de doğru basılması için ölçek yeterlidir.
    /// </summary>
    public static class ScaleStandardCommands
    {
        public static object SetScale(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;
            int scale = Util.GetInt(p, "scale", 50);
            string viewName = Util.GetString(p, "view", null);

            View view = ResolveView(doc, app, viewName);
            if (view == null)
                return new { applied = false, message = "Uygun görünüm bulunamadı." };

            bool hasTemplate = view.ViewTemplateId != ElementId.InvalidElementId;
            using (var t = new Transaction(doc, "1/50 standardı uygula"))
            {
                t.Start();
                // Görünüm şablonu ölçeği kilitliyorsa Scale set'i sessizce yutulur.
                try { view.Scale = scale; } catch { }
                try { view.DetailLevel = ViewDetailLevel.Fine; } catch { }
                t.Commit();
            }

            return new
            {
                applied = true,
                view = view.Name,
                scale = view.Scale,
                detail_level = view.DetailLevel.ToString(),
                has_view_template = hasTemplate,
                note = hasTemplate
                    ? "Görünümde şablon var; ölçek şablonda kilitliyse değişmemiş olabilir."
                    : "1:" + scale + " ölçeğinde anotasyonlar kâğıt boyutuyla ölçeklenir."
            };
        }

        internal static View ResolveView(Document doc, UIApplication app, string viewName)
        {
            if (!string.IsNullOrEmpty(viewName))
            {
                return new FilteredElementCollector(doc).OfClass(typeof(View))
                    .Cast<View>().FirstOrDefault(v => !v.IsTemplate && v.Name == viewName);
            }
            return app.ActiveUIDocument.ActiveView;
        }
    }
}
