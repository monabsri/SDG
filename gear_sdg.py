# - Uses labels authored in the GUI/USDs (do NOT relabel in code)

from omni.isaac.kit import SimulationApp
import os, argparse, random

parser = argparse.ArgumentParser("Gear dataset generator")
parser.add_argument("--headless", type=bool, default=True)
parser.add_argument("--height", type=int, default=640)
parser.add_argument("--width",  type=int, default=640)
parser.add_argument("--num_frames", type=int, default=10000, help="total frames")
parser.add_argument("--data_dir", type=str, default=os.getcwd() + "/synthetic_images")
parser.add_argument("--mode", type=str, default="batch",
                    choices=["batch","mix","all"],
                    help="batch: one model per batch; mix: one random model per frame; all: all models visible")
parser.add_argument("--renderer", type=str, default="PathTracing",
                    choices=["RayTracedLighting","PathTracing"])
parser.add_argument("--gear_usds", nargs="*", default=[
    os.path.join(os.getcwd(), "Gear1_var1.usdc"),
    os.path.join(os.getcwd(), "Gear1_var2.usdc"),
    os.path.join(os.getcwd(), "Gear1_var3.usdc"),
    os.path.join(os.getcwd(), "Gear1_var4.usdc"),
    os.path.join(os.getcwd(), "Gear1_var5.usdc"),
    os.path.join(os.getcwd(), "Gear1_var6.usdc"),
    os.path.join(os.getcwd(), "Gear2_var1.usdc"),
    os.path.join(os.getcwd(), "Gear2_var2.usdc"),
    os.path.join(os.getcwd(), "Gear2_var3.usdc"),
    os.path.join(os.getcwd(), "Gear2_var4.usdc"),
    os.path.join(os.getcwd(), "Gear1_rust.usd"),
    os.path.join(os.getcwd(), "Gear2_rust.usd"),
    os.path.join(os.getcwd(), "Gear1.usdc"),
    os.path.join(os.getcwd(), "Gear1_ok_1.usdc"),
    os.path.join(os.getcwd(), "Gear1_ok_2.usdc"),
    os.path.join(os.getcwd(), "Gear1_ok_3.usdc"),
    os.path.join(os.getcwd(), "Gear1_ok_4.usdc"),
    os.path.join(os.getcwd(), "Gear1_ok_5.usdc"),
    os.path.join(os.getcwd(), "Gear2.usdc"),
], help="Paths to gear USDs")
args, _ = parser.parse_known_args()

CONFIG = {
    "renderer": args.renderer,
    "headless": args.headless,
    "width": args.width,
    "height": args.height,
}
simulation_app = SimulationApp(launch_config=CONFIG)

# ---- imports after app starts ----
import carb, omni, omni.usd, omni.replicator.core as rep
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import get_current_stage, open_stage



def prefix_with_isaac_asset_server(rel):
    root = get_assets_root_path()
    if not root:
        raise RuntimeError("Nucleus not found")
    return root + rel

def step_until_done():
    """Run the current orchestrator trigger until it finishes."""
    rep.orchestrator.run()
    while not rep.orchestrator.get_is_started():
        simulation_app.update()
    while rep.orchestrator.get_is_started():
        simulation_app.update()
    rep.BackendDispatch.wait_until_done()
    rep.orchestrator.stop()
    simulation_app.update()

def main():
    # Open a simple environment
    omni.usd.get_context().get_stage()
    for _ in range(60):
        simulation_app.update()

    with rep.new_layer():
        # ---------- Load ALL gear USDs (defective variants) ----------
        usd_list = list(args.gear_usds)
        for p in usd_list:
            if not os.path.exists(p):
                carb.log_warn(f"[WARN] USD not found on disk: {p}")

        gear_refs = [rep.create.from_usd(p) for p in usd_list]
        for _ in range(40):
            simulation_app.update()  # let composition settle

        if len(gear_refs) != len(usd_list):
            carb.log_warn(f"[WARN] created {len(gear_refs)} refs but passed {len(usd_list)} paths")

        # ---------- Camera ----------
        cam = rep.create.camera(clipping_range=(0.1, 1_000_000))

        # ---------- Materials (simple metal bank) ----------
        machined_steel = rep.create.material_omnipbr(diffuse=rep.distribution.uniform((0.42,0.42,0.44),(0.52,0.52,0.56)), metallic=1.0, roughness=rep.distribution.uniform(0.20, 0.32), specular=rep.distribution.uniform(0.45,0.55),)
        dark_steel     = rep.create.material_omnipbr(diffuse=(0.28,0.28,0.30), metallic=1.0, roughness=rep.distribution.uniform(0.22, 0.35), specular=rep.distribution.uniform(0.40,0.50),)
        stainless      = rep.create.material_omnipbr(diffuse=(0.62,0.62,0.64), metallic=1.0, roughness=rep.distribution.uniform(0.15,0.25), specular=rep.distribution.uniform(0.45,0.55),)
        random_metals  = rep.create.material_omnipbr(
            diffuse= rep.distribution.uniform((0.25, 0.25, 0.25),(0.45, 0.45, 0.45)),
            metallic=1.0, roughness=rep.distribution.uniform(0.10,0.55), specular=rep.distribution.uniform(0.40,0.85))
        #oxidized_iron = rep.create.material_omnipbr(diffuse=rep.distribution.uniform((0.35, 0.33, 0.32),(0.45,0.42,0.40)), metallic=1.0, roughness=rep.distribution.uniform(0.22, 0.35), specular=rep.distribution.uniform(0.30,0.40),)
        material_bank = [random_metals]

        # ---------- Lights ----------   
        def sphere_lights():
            mode = random.choice(["sunny", "overcast", "indoor_soft"])
            if mode == "sunny":
                rep.create.light(light_type="distant", rotation=rep.distribution.uniform((10, -180, 0), (55, 180, 0)), intensity=rep.distribution.uniform(1800, 4500), color=rep.distribution.uniform((0.92,0.90,0.88),(1.0,0.98,0.96)),)
                rep.create.light(light_type="dome", intensity=rep.distribution.uniform(250, 700), color=rep.distribution.uniform((0.93,0.93,0.93),(1.0,1.0,1.0)),)
            elif mode == "overcast":
                rep.create.light(light_type="dome", intensity=rep.distribution.uniform(200,1200), )
            elif mode == "indoor_soft":
                rep.create.light(light_type="rect", position=(0.4, -0.5, 0.7), rotation=(60, 0, -40), intensity=rep.distribution.uniform(800, 3500), scale=(0.6, 0.6, 1.0), color=rep.distribution.uniform((0.95,0.88,0.80),(1.0,1.0,1.0)),)
                rep.create.light(light_type="dome", intensity=rep.distribution.uniform(50, 400), color=rep.distribution.uniform((0.93,0.93,0.93),(1.0,1.0,1.0)),)

        rep.randomizer.register(sphere_lights)

        # ---------- Writer ----------
        render_product = rep.create.render_product(cam, (args.width, args.height))
        rep.annotators.get("rgb").attach(render_product)
        rep.annotators.get("instance_segmentation").attach(render_product)

        

        from yolo_writer import YOLOWriter
        rep.WriterRegistry.register(YOLOWriter)
        class_mapping = { "defect": 0, "rust": 1, "ok": 2}
        writer=rep.WriterRegistry.get("YOLOWriter")
      

        writer=YOLOWriter(output_dir=args.data_dir,
                         rgb=True, bounding_box_2d_tight=True,
                         image_output_format="png",
                         class_mapping=class_mapping,
                         min_bbox_area=0.001,
                         min_mask_area=0.001,
                         max_points=100,
                         instance_segmentation=True,
                         )


        writer.attach([render_product])
        # ----------Background --------
        plane=rep.create.plane(scale=4, visible=True)
        bg_mat = rep.create.material_omnipbr(metallic=0.0, roughness=0.5)
        plane.material=bg_mat
        wood_diffuses = [
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/laminate_oak_diffuse.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/osb_wood_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/fineline_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/beech_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/beech_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/pine_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/wood_ash_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Wood/textures/wood_oak_mountain_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Paper/textures/cardboard_new_01_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Plastic/textures/pcb_solder_mask_grey_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Carpet/textures/carpet_rough_woven_diff.jpg",
            "/opt/nvidia/mdl/vMaterials_2/Concrete/textures/spongy_concrete_weathered_diff.jpg",
            os.path.join(os.getcwd(), "wood1.jpg"),
            os.path.join(os.getcwd(), "wood2.jpg"),
        ]
        def random_background():
            with plane:
                rep.randomizer.texture(
                    textures=wood_diffuses,
                    
                )
                rep.modify.pose(position=(0,0,0), rotation=(0,0,0))
            return plane
        rep.randomizer.register(random_background)

        # ---------- Helpers ----------
        n_models = max(1, len(gear_refs))

        def show_only(idx: int):
            for i, g in enumerate(gear_refs):
                with g:
                    rep.modify.visibility(i == idx)

        def show_all():
            for g in gear_refs:
                with g:
                    rep.modify.visibility(True)

        def randomize_camera_and_lights():
            global frame_counter
            #mode = random.choice(["top", "low"])
            with cam:
                rep.modify.attribute("focalLength",rep.distribution.uniform(20.0, 45.0))
                rep.modify.pose(
                    position=rep.distribution.choice([
                        (0.0,0.0,4.2),
                        (0.65,-1.8,1.15),
                    ]),
                    look_at=rep.distribution.choice([
                        (0.0, 0.0, 0.25),
                        (0.0, 0.0, 0.30),
                    ]),
                )

            rep.randomizer.sphere_lights()

        def randomize_one_gear(g):
            with g:
                rep.modify.pose(
                    position=rep.distribution.uniform(
                        (-0.03, -0.03, 0.45),
                        (0.03, 0.03, 0.50)
                    ),
                    rotation=rep.distribution.uniform(
                        (0, 0.0, 0), (0, 95.0, 360),
                    ),
                    scale=rep.distribution.uniform(0.98, 1.02),
                )
    
                rep.randomizer.materials(material_bank)

        # ---------- MODES ----------
        if args.mode == "mix":
            print(f"[info] MIX mode: {args.num_frames} frames total (one random model per frame)")

            @rep.randomizer
            def pick_and_show_one():
                # hide all
                for g in gear_refs:
                    with g:
                        rep.modify.visibility(False)
                # show one random gear
                chosen = rep.distribution.choice(gear_refs)
                with chosen:
                    rep.modify.visibility(True)
                return chosen

            with rep.trigger.on_frame(num_frames=args.num_frames):
                pick_and_show_one()
                rep.randomizer.random_background()
                randomize_camera_and_lights()
                for g in gear_refs:  # only the visible one matters
                    randomize_one_gear(g)

            step_until_done()

        elif args.mode == "all":
            print(f"[info] ALL mode: {args.num_frames} frames, all {n_models} visible")
            show_all()

            with rep.trigger.on_frame(num_frames=args.num_frames):
                rep.randomizer.random_background()
                randomize_camera_and_lights()
                for g in gear_refs:
                    randomize_one_gear(g)

            step_until_done()

        else:  # batch
            base = args.num_frames // n_models
            rem  = args.num_frames %  n_models
            order = list(range(n_models))
            random.shuffle(order)
            print(f"[info] BATCH mode: order={order}, base={base}, remainder={rem}")

            for pos, idx in enumerate(order):
                frames = base + (1 if pos < rem else 0)
                if frames <= 0:
                    print(f"[skip] model {idx} gets 0 frames (increase --num_frames).")
                    continue

                print(f"[batch] {frames} frames of model index {idx}")
                show_only(idx)

                with rep.trigger.on_frame(num_frames=frames):
                    randomize_camera_and_lights()
                    rep.randomizer.random_background()
                    randomize_one_gear(gear_refs[idx])

                step_until_done()

    simulation_app.update()

if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
