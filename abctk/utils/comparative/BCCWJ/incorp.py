import logging

logger = logging.getLogger(__name__)

from abctk.obj.comparative import ABCTComp_BCCWJ_ID
from abctk.utils.comparative.BCCWJ.loader import BCCWJSentIndex

IDX_READ_ALSO: dict[BCCWJSentIndex, tuple[BCCWJSentIndex]] = {
    BCCWJSentIndex("LBf9_00090", 18640): (BCCWJSentIndex("LBf9_00090", 18760),),
    BCCWJSentIndex("LBn9_00128", 15510): (BCCWJSentIndex("LBn9_00128", 15580),),
}


def get_real_text(
    idx: BCCWJSentIndex,
    real_texts: dict[BCCWJSentIndex, str],
    corpus_id: ABCTComp_BCCWJ_ID | str | None = None,
) -> str | None:
    corpus_id_str = str(corpus_id) or "[UNKNOWN]"

    if real_text := real_texts.get(
        BCCWJSentIndex(
            idx.sampleID,
            idx.sent_start_pos,
        )
    ):
        result = real_text

        for idx_next in IDX_READ_ALSO.get(idx, ()):
            next_real_text = real_texts.get(
                BCCWJSentIndex(
                    idx_next.sampleID,
                    idx_next.sent_start_pos,
                ),
                "",
            )

            if next_real_text:
                result += next_real_text
                logger.info(
                    f"Concatenated the next real text {idx_next} for {corpus_id_str}"
                )
            else:
                logger.info(
                    f"Cannot find the next real text {idx_next} for {corpus_id_str}"
                )
        return result
    else:
        logger.warning(f"Cannot find the real text for {corpus_id_str}")
        return None
