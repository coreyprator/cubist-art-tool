#!/usr/bin/env python3
"""Fix CLI main function to use same logic as working run_pipeline"""

from pathlib import Path


def fix_cli_main():
    """Update CLI main() to use the same plugin discovery as run_pipeline"""

    cli_file = Path("cubist_cli.py")
    content = cli_file.read_text(encoding="utf-8")

    # Find the main() function and replace the geometry execution logic
    lines = content.split("\n")
    fixed_lines = []
    in_main_render_section = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for the start of the render section in main()
        if "Run geometry and export" in line or (
            "doc = None" in line and "main()" in content[: content.find(line)]
        ):
            in_main_render_section = True
            fixed_lines.append(line)
            i += 1
            continue

        # Replace the render section with working logic
        if in_main_render_section and (
            'if hasattr(geom_mod, "render")' in line or "doc = geom_mod.render" in line
        ):
            # Replace entire render section with working logic from run_pipeline
            indent = len(line) - len(line.lstrip())

            new_render_logic = [
                " " * indent + "# Generate shapes using multiple candidate methods",
                " " * indent + "doc_or_shapes = None",
                " " * indent
                + 'render_candidates = ("render", "generate", "render_shapes", "run", "build", "make", "create")',
                " " * indent + "",
                " " * indent + "# Get canvas size for plugins that need it",
                " " * indent + "canvas_size = None",
                " " * indent + "try:",
                " " * indent + "    from PIL import Image",
                " " * indent + "    with Image.open(str(inp)) as img:",
                " " * indent + "        canvas_size = img.size",
                " " * indent + "except Exception:",
                " " * indent + "    canvas_size = (1200, 800)",
                " " * indent + "",
                " " * indent + "for cand in render_candidates:",
                " " * indent + "    if hasattr(geom_mod, cand):",
                " " * indent + "        try:",
                " " * indent + "            import inspect",
                " " * indent + "            fn = getattr(geom_mod, cand)",
                " " * indent + "            sig = inspect.signature(fn)",
                " " * indent + "            kwargs = {}",
                " " * indent + "            ",
                " " * indent + "            # Add parameters that the function accepts",
                " " * indent + '            if "points" in sig.parameters:',
                " " * indent + '                kwargs["points"] = args.points',
                " " * indent + '            if "seed" in sig.parameters:',
                " " * indent + '                kwargs["seed"] = args.seed',
                " " * indent + '            if "cascade_stages" in sig.parameters:',
                " " * indent
                + '                kwargs["cascade_stages"] = args.cascade_stages',
                " " * indent + '            if "canvas_size" in sig.parameters:',
                " " * indent + '                kwargs["canvas_size"] = canvas_size',
                " " * indent + "            ",
                " " * indent + "            # Call with appropriate parameters",
                " " * indent + '            if cand == "render":',
                " " * indent + "                doc_or_shapes = fn(str(inp), **kwargs)",
                " " * indent + "            else:",
                " " * indent + "                doc_or_shapes = fn(**kwargs)",
                " " * indent + "            break",
                " " * indent + "        except Exception as e:",
                " " * indent + "            continue",
            ]

            # Add the new logic
            for new_line in new_render_logic:
                fixed_lines.append(new_line)

            # Skip the old render logic until we find the export section
            while i < len(lines) and "if args.export_svg:" not in lines[i]:
                i += 1

            # Now handle the export section
            if i < len(lines) and "if args.export_svg:" in lines[i]:
                export_indent = len(lines[i]) - len(lines[i].lstrip())

                new_export_logic = [
                    " " * export_indent + "if args.export_svg:",
                    " " * export_indent + "    # Try plugin exporters first",
                    " " * export_indent + "    exported = False",
                    " " * export_indent + "    ",
                    " " * export_indent
                    + '    for export_name in ("export_svg", "save_svg", "write_svg"):',
                    " " * export_indent + "        if hasattr(geom_mod, export_name):",
                    " " * export_indent + "            try:",
                    " " * export_indent
                    + "                getattr(geom_mod, export_name)(doc_or_shapes, str(expected_svg))",
                    " " * export_indent + "                exported = True",
                    " " * export_indent + "                break",
                    " " * export_indent + "            except Exception:",
                    " " * export_indent + "                continue",
                    " " * export_indent + "    ",
                    " " * export_indent + "    # Try document object exporter",
                    " " * export_indent
                    + '    if not exported and hasattr(doc_or_shapes, "write_svg"):',
                    " " * export_indent + "        try:",
                    " " * export_indent
                    + "            doc_or_shapes.write_svg(str(expected_svg))",
                    " " * export_indent + "            exported = True",
                    " " * export_indent + "        except Exception:",
                    " " * export_indent + "            pass",
                    " " * export_indent + "    ",
                    " " * export_indent + "    # Fallback to svg_export module",
                    " " * export_indent + "    if not exported:",
                    " " * export_indent + "        try:",
                    " " * export_indent + "            import svg_export",
                    " " * export_indent
                    + "            svg_content = svg_export.export_svg(doc_or_shapes, width=canvas_size[0], height=canvas_size[1])",
                    " " * export_indent
                    + "            with open(str(expected_svg), 'w', encoding='utf-8') as f:",
                    " " * export_indent + "                f.write(svg_content)",
                    " " * export_indent + "            exported = True",
                    " " * export_indent + "        except Exception as e:",
                    " " * export_indent
                    + '            raise RuntimeError(f"No working exporter found: {e}")',
                    " " * export_indent + "    ",
                    " " * export_indent + "    if not exported:",
                    " " * export_indent
                    + '        raise RuntimeError("No exporter found in geometry module")',
                ]

                for new_line in new_export_logic:
                    fixed_lines.append(new_line)

                # Skip the old export logic
                while i < len(lines) and not (
                    lines[i].strip() == ""
                    or "Verify file was written" in lines[i]
                    or lines[i].startswith('    info["elapsed_s"]')
                ):
                    i += 1
                i -= 1  # Back up one so we don't skip the next section

            in_main_render_section = False
        else:
            fixed_lines.append(line)

        i += 1

    # Write the fixed content
    cli_file.write_text("\n".join(fixed_lines), encoding="utf-8")
    print("Fixed CLI main() function to use same logic as working run_pipeline")
    return True


if __name__ == "__main__":
    fix_cli_main()
