#include "text_block_utils.h"
#include "indent_funcs.h"

#include "alg_impl.h"

namespace Qutepart {

void IndentAlgImpl::setConfig(int width, bool useTabs) {
    width_ = width;
    useTabs_ = useTabs;
}

void IndentAlgImpl::setLanguage(const QString& language) {
    language_ = language;
}

QString IndentAlgImpl::autoFormatLine(QTextBlock block) const {
    return computeSmartIndent(block, -1) + stripLeftWhitespace(block.text());
}

QString IndentAlgImpl::indentLine(QTextBlock block, int cursorPos) const {
    QString indent = computeSmartIndent(block, cursorPos);
    if ( ! indent.isNull()) {
        return indent + stripLeftWhitespace(block.text());
    } else {
        return block.text();
    }
}

QString IndentAlgImpl::computeSmartIndent(QTextBlock block, int cursorPos) const {
    return "";
}


const QString& IndentAlgImpl::triggerCharacters() const {
    static const QString NULL_STRING = QString::null;
    return NULL_STRING;
}

QString IndentAlgImpl::indentText() const {
    return makeIndent(width_, useTabs_);
}

};  // namespace Qutepart
