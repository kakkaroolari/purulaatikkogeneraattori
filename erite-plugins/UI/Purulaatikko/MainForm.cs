
using System.Windows.Forms;
using System;
using System.Collections.Generic;
using System.Linq;
using EritePlugins.Common;
using Tekla.Structures.Catalogs;
using Tekla.Structures.Dialog;

namespace EritePlugins.UI.Purulaatikko 
{
    /*
     * cp ~/devel/purulaatikkogeneraattori/erite-plugins/Common/bin/Debug/EritePlugins.Common.dll ~/devel/purulaatikkogeneraattori/erite-plugins/Core/bin/Debug/EritePlugins.Core.dll ~/devel/purulaatikkogeneraattori/erite-plugins/UI/bin/Debug/EritePlugins.UI.dll ~/devel/Tekla/
     * cp ~/source/repos/purulaatikkogeneraattori/erite-plugins/UI/bin/Debug/EritePlugins.*.dll  ~/devel/Tekla/ -v
     */
    public partial class MainForm : PluginFormBase
   {
      public MainForm()
      {
         InitializeComponent();
      }

        private void buttonOk_Click(object sender, EventArgs e)
        {
            this.Apply();
            this.Close();
        }

        private void buttonModify_Click(object sender, EventArgs e)
        {
            this.Modify();
        }
    }
}



