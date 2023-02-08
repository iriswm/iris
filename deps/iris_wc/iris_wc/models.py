from django.db import models
from django.utils.translation import gettext_lazy as _

from iris.app.models import CancelableMixin, NotesMixin, TimestampMixin, add_note_type


class Order(TimestampMixin, CancelableMixin, NotesMixin, models.Model):
    wc_order_id = models.IntegerField(_("WooCommerce order ID"))
    wc_order_notes = models.TextField(_("WooCommerce order notes"), blank=True)

    def cancel(reason):
        super().cancel(reason)
        for line in self.lines.all():
            line.cancel(reason)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __str__(self):
        return _("WooCommerce order {obj.wc_order_id}").format(obj=self)


add_note_type("WooCommerce order", "iris_wc.Order")


class WooCommerceCategoryMixin(models.Model):
    wc_category_id = models.IntegerField(_("WooCommerce category ID"))

    class Meta:
        abstract = True


class Line(
    TimestampMixin, CancelableMixin, NotesMixin, WooCommerceCategoryMixin, models.Model
):
    order = models.ForeignKey(
        "Order",
        verbose_name=_("order"),
        on_delete=models.CASCADE,
        related_name="lines",
    )
    process = models.ForeignKey(
        "iris.Process",
        verbose_name=_("process"),
        on_delete=models.SET_NULL,
        related_name="woocommerce_lines",
        null=True,
        blank=True,
    )
    wc_order_item_id = models.IntegerField(_("WooCommerce order line ID"))

    class Meta:
        verbose_name = _("line")
        verbose_name_plural = _("lines")

    def __str__(self):
        return str(
            _(
                f"WooCommerce line {self.wc_order_item_id} for order {self.order.wc_order_id}"
            )
        )


add_note_type("WooCommerce line", "iris_wc.Line")


class ProductMap(models.Model):
    wc_product_id = models.IntegerField(_("WooCommerce product ID"))
    process = models.ForeignKey(
        "iris.Process",
        verbose_name=_("process"),
        on_delete=models.CASCADE,
        related_name="mapped_woocommerce_products",
    )

    class Meta:
        verbose_name = _("product map")
        verbose_name_plural = _("product maps")

    def __str__(self):
        return str(
            _(
                f"Map: WooCommerce product {self.wc_product_id} -> Process {self.process}"
            )
        )


class CategoryMap(WooCommerceCategoryMixin, models.Model):
    process = models.ForeignKey(
        "iris.Process",
        verbose_name=_("process"),
        on_delete=models.CASCADE,
        related_name="mapped_woocommerce_categories",
    )

    class Meta:
        verbose_name = _("category map")
        verbose_name_plural = _("category maps")

    def __str__(self):
        return str(
            _(
                f"Map: WooCommerce category {self.wc_category_id} -> Process {self.process}"
            )
        )
