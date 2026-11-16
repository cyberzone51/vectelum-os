import importlib.util, tempfile, unittest, json
from pathlib import Path
from unittest.mock import patch, Mock

p=Path(__file__).with_name("vectelum-local.py")
spec=importlib.util.spec_from_file_location("launcher",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class LauncherTests(unittest.TestCase):
    def test_reject_wrong_image(self):
        with patch.object(m,"check_docker"),patch.object(m,"inspect",return_value={"Config":{"Image":"unrelated"}}),patch.object(m,"docker") as d:
            with self.assertRaises(RuntimeError): m.start_backend()
            d.assert_not_called()
    def test_existing_starts_only_core(self):
        def obj(n):
            return None if n=="nomad_updater" else {"Config":{"Image":m.IMAGE},"State":{"Running":True}}
        with patch.object(m,"check_docker"),patch.object(m,"inspect",side_effect=obj),patch.object(m,"docker") as d,patch.object(m,"wait_ready"):
            m.start_backend()
            self.assertEqual([x.args for x in d.call_args_list],[("start",n) for n in m.CORE])
    def test_legacy_compatible_backend(self):
        def obj(n):
            return None if n=="nomad_updater" else {"Config":{"Image":"vectelum-os:56350b3"},"State":{"Running":True}}
        with patch.object(m,"check_docker"),patch.object(m,"inspect",side_effect=obj),patch.object(m,"docker") as d,patch.object(m,"wait_ready"):
            m.start_backend()
            self.assertEqual([x.args for x in d.call_args_list],[("start",n) for n in m.CORE])
    def test_fresh_refuses_existing(self):
        with patch.object(m,"check_docker"),patch.object(m,"inspect",return_value={ "existing":True }),patch.object(m,"docker") as d:
            with self.assertRaises(RuntimeError): m.fresh_backend()
            d.assert_not_called()
    def test_fresh_compose(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"backend"
            with patch.object(m,"DATA",root),patch.object(m,"check_docker"),patch.object(m,"inspect",return_value=None),patch.object(m,"docker") as d,patch.object(m,"run") as runner,patch.object(m,"wait_ready"),patch.object(m.shutil,"disk_usage",return_value=Mock(free=40*1024**3)):
                m.fresh_backend()
            c=json.loads((root/"compose.json").read_text())
            self.assertEqual(c["services"]["admin"]["image"],m.IMAGE)
            self.assertIn(m.REVISION,runner.call_args_list[1].args[0])
            self.assertIn("VERSION=1.35.1-vectelum.2",d.call_args_list[0].args)
            self.assertEqual(c["services"]["admin"]["ports"],["127.0.0.1:8080:8080"])
            self.assertNotIn("updater",c["services"])
            self.assertEqual(c["services"]["admin"]["environment"]["DB_PASSWORD"],c["services"]["mysql"]["environment"]["MYSQL_PASSWORD"])
            self.assertNotEqual(c["services"]["mysql"]["environment"]["MYSQL_PASSWORD"],c["services"]["mysql"]["environment"]["MYSQL_ROOT_PASSWORD"])
    def test_invalid_uri(self):
        with patch.object(m.sys,"argv",["launcher.py","vectelum://launch?cmd=test"]),patch.object(m,"launch") as launch:
            with self.assertRaises(SystemExit): m.main()
            launch.assert_not_called()

if __name__=="__main__": unittest.main()
