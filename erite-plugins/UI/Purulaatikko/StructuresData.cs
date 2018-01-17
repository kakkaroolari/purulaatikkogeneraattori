using EritePlugins.Common;

namespace EritePlugins.UI.Purulaatikko 
{
   using Tekla.Structures.Plugins;

   public class StructuresData
   {
      [StructuresField("PartsAttributeFile")]
      public string PartsAttributeFile;

      public bool ShowWarnings()
      {
         return false;
      }
   }
}
