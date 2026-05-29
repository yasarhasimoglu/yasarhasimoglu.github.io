using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>
    /// Mahal (oda) etiketleri yerleştirir ve isteğe bağlı olarak mahal isimlerini ayarlar.
    /// Etiket; mahal adı + numara + alanı 1/50 standardına uygun gösterir.
    /// </summary>
    public static class RoomTagCommands
    {
        public static object TagRooms(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;
            View view = ScaleStandardCommands.ResolveView(doc,
                app, Util.GetString(p, "view", null));

            if (!(view is ViewPlan))
                throw new InvalidOperationException("Mahal etiketi için aktif görünüm bir plan olmalı.");

            // İsteğe bağlı yeniden adlandırma haritası: [{ "number": "101", "name": "OTURMA ODASI" }]
            var renameByNumber = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            var renameById = new Dictionary<long, string>();
            if (Util.TryGetArray(p, "names", out var names))
            {
                foreach (var n in names.EnumerateArray())
                {
                    string name = n.TryGetProperty("name", out var nm) ? nm.GetString() : null;
                    if (string.IsNullOrEmpty(name)) continue;
                    if (n.TryGetProperty("number", out var num) && num.ValueKind == JsonValueKind.String)
                        renameByNumber[num.GetString()] = name;
                    if (n.TryGetProperty("id", out var idv) && idv.ValueKind == JsonValueKind.Number)
                        renameById[idv.GetInt64()] = name;
                }
            }

            var rooms = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .Cast<Room>()
                .Where(r => r.Area > 0)
                .ToList();

            int tagged = 0, renamed = 0;
            var tagResults = new List<object>();

            using (var t = new Transaction(doc, "Mahal etiketleri ve isimleri"))
            {
                t.Start();

                foreach (var room in rooms)
                {
                    // İsim güncelleme
                    string newName = null;
                    if (room.Number != null && renameByNumber.TryGetValue(room.Number, out var byNum))
                        newName = byNum;
                    else if (renameById.TryGetValue(room.Id.Value, out var byId))
                        newName = byId;
                    if (newName != null)
                    {
                        room.get_Parameter(BuiltInParameter.ROOM_NAME).Set(newName);
                        renamed++;
                    }

                    // Zaten etiketli mi?
                    bool alreadyTagged = new FilteredElementCollector(doc, view.Id)
                        .OfCategory(BuiltInCategory.OST_RoomTags)
                        .WhereElementIsNotElementType()
                        .Cast<RoomTag>()
                        .Any(rt => rt.Room != null && rt.Room.Id == room.Id);
                    if (alreadyTagged) continue;

                    if (room.Location is LocationPoint lp)
                    {
                        var uv = new UV(lp.Point.X, lp.Point.Y);
                        RoomTag rt = doc.Create.NewRoomTag(new LinkElementId(room.Id), uv, view.Id);
                        tagged++;
                        tagResults.Add(new { tag_id = rt.Id.Value, room = room.Name,
                            number = room.Number, area_m2 = Util.Round(Util.SqFtToSqM(room.Area)) });
                    }
                }

                t.Commit();
            }

            return new { room_count = rooms.Count, tagged, renamed, tags = tagResults };
        }
    }
}
