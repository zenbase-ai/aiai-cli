# Generated by Django 5.2 on 2025-04-23 01:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DiscoveredRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rule_type", models.TextField(default="")),
                ("rule_text", models.TextField(default="")),
                ("function_name", models.TextField(default="")),
                ("file_path", models.TextField(default="")),
                ("target_code_section", models.TextField(default="")),
                ("confidence", models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name="OtelSpan",
            fields=[
                ("trace_id", models.TextField()),
                ("span_id", models.TextField(db_index=True, primary_key=True, serialize=False)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("attributes", models.JSONField()),
                ("prompt", models.TextField()),
                ("completion", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="SyntheticDatum",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("input_data", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="SyntheticEval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "kind",
                    models.CharField(choices=[("rules", "Rules"), ("head_to_head", "Head To Head")], max_length=20),
                ),
                ("prompt", models.TextField()),
                ("fields", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="FunctionInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("file_path", models.CharField(max_length=512)),
                ("line_start", models.IntegerField()),
                ("line_end", models.IntegerField()),
                ("signature", models.TextField()),
                ("source_code", models.TextField()),
                ("docstring", models.TextField(blank=True, null=True)),
                ("comments", models.JSONField(blank=True, null=True)),
                ("string_literals", models.JSONField(blank=True, null=True)),
                ("variables", models.JSONField(blank=True, null=True)),
                ("constants", models.JSONField(blank=True, null=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["name"], name="app_functio_name_877854_idx"),
                    models.Index(fields=["file_path"], name="app_functio_file_pa_12a69d_idx"),
                ],
                "unique_together": {("file_path", "name", "line_start")},
            },
        ),
        migrations.CreateModel(
            name="DataFileInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_path", models.CharField(max_length=500, unique=True)),
                ("file_type", models.CharField(max_length=10)),
                ("content", models.TextField(blank=True, null=True)),
                ("reference_contexts", models.JSONField(blank=True, default=list, null=True)),
                ("last_analyzed", models.DateTimeField(auto_now=True)),
                ("referenced_by", models.ManyToManyField(blank=True, to="app.functioninfo")),
            ],
        ),
        migrations.CreateModel(
            name="EvalRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trace_id", models.TextField()),
                ("input_data", models.TextField()),
                ("output_data", models.TextField()),
                ("reward", models.TextField(blank=True)),
                (
                    "eval",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="app.syntheticeval"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DataFileAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_valid_reference", models.BooleanField(default=False)),
                ("file_purpose", models.TextField(blank=True, null=True)),
                ("content_category", models.CharField(blank=True, max_length=50, null=True)),
                ("confidence_score", models.FloatField(default=0.0)),
                ("analysis_date", models.DateTimeField(auto_now=True)),
                (
                    "data_file",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="analysis", to="app.datafileinfo"
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["is_valid_reference"], name="app_datafil_is_vali_a57352_idx"),
                    models.Index(fields=["content_category"], name="app_datafil_content_473bd0_idx"),
                ],
            },
        ),
        migrations.AddIndex(
            model_name="datafileinfo",
            index=models.Index(fields=["file_type"], name="app_datafil_file_ty_30471e_idx"),
        ),
        migrations.AddIndex(
            model_name="datafileinfo",
            index=models.Index(fields=["file_path"], name="app_datafil_file_pa_dec686_idx"),
        ),
    ]
